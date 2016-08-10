/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/* ************************************************************************

#asset(gosa/*)

************************************************************************ */

qx.Class.define("gosa.view.Search",
{
  extend : qx.ui.tabview.Page,

  construct : function()
  {
    this._sq = [];
    var barWidth = 200;

    // Default search parameters
    this.__default_selection = this.__selection = {
        'fallback': true,
        'secondary': "enabled",
        'category': "all",
        'mod-time': "all"
    };
    this._categories = {};
    var d = new Date();
    this.__now = d.getTime() / 1000 + d.getTimezoneOffset() * 60;

    // Call super class and configure ourselfs
    this.base(arguments, "", gosa.Config.getImagePath("apps/search.png", 32));
    this.getChildControl("button").getChildControl("label").exclude();
    this.setLayout(new qx.ui.layout.VBox(5));

    // Create search field / button
    var searchHeader = new qx.ui.container.Composite();
    var searchLayout = new qx.ui.layout.HBox(10);
    searchHeader.setLayout(searchLayout);

    var sf = new qx.ui.form.TextField('');
    sf.setPlaceholder(this.tr("Please enter your search..."));
    this.addListener("resize", function() {
      sf.setWidth(parseInt(this.getBounds().width / 2));
    }, this);
    searchHeader.add(sf);

    var sb = new qx.ui.form.Button(this.tr("Search"));
    searchHeader.add(sb);
    searchHeader.setPadding(20);
    searchHeader.setPaddingBottom(0);

    searchLayout.setAlignX("center");

    this.add(searchHeader);

    // Create search info (hidden)
    this.searchInfo = new qx.ui.container.Composite(new qx.ui.layout.HBox(10));
    this.searchInfo.hide();
    this.searchInfo.setPadding(20);
    var sil = new qx.ui.basic.Label(this.tr("Search"));
    sil.setTextColor("red");
    sil.setFont(qx.bom.Font.fromString("20px Sans Serif"));
    sil.setWidth(barWidth);
    this.searchInfo.add(sil);

    this.sii = new qx.ui.basic.Label();
    this.sii.setTextColor("gray");
    this.sii.setAlignY("bottom");
    this.searchInfo.add(this.sii);

    this.add(this.searchInfo);

    // Create search result
    this.searchResult = new qx.ui.container.Composite(new qx.ui.layout.Canvas);
    this.searchResult.hide();
    this.searchResult.setPadding(20);
    this.searchResult.setDecorator("separator-vertical");
    this.resultList = new qx.ui.list.List();
    this.resultList.setModel(new qx.data.Array());
    this.resultList.setAppearance("SearchList");
    this.resultList.setDecorator(null);
    this.searchResult.add(this.resultList, {left: barWidth, right: 0, bottom: 0, top: 0});

    // Create search aid bar on the left
    this.searchAid = new gosa.ui.SearchAid();
    this.searchAid.setWidth(barWidth);
    this.searchResult.add(this.searchAid, {left: 0, bottom: 0, top: 0});
    this.searchAid.addListener("filterChanged", this.updateFilter, this);

    this.add(this.searchResult, {flex: 1});

    // Bind search methods
    sb.addListener("execute", function(){
        this._old_query = "";
        this.doSearchE();
      }, this);
    sf.addListener("keyup", this._handle_key_event, this);
    this.sf = sf;

    // Bind search result model
    var that = this;
    var deltas = {'hour': 60*60, 'day': 60*60*24 , 'week': 60*60*24*7, 'month': 2678400, 'year': 31536000};
    this.resultList.setDelegate({
        createItem: function(){

          var item = new gosa.ui.SearchListItem();
          item.addListener("edit", function(e){
              item.setIsLoading(true);
              that.openObject(e.getData().getDn());
              that.addListenerOnce("loadingComplete", function(e){
                  if(e.getData()['dn'] == item.getDn()){
                    item.setIsLoading(false);
                  }
                }, that);
            }, this);

          item.addListener("remove", function(e){
              var dialog = new gosa.ui.dialogs.RemoveObject(e.getData().getDn());
              dialog.addListener("remove", function(){
                  that.removeObject(item.getUuid());
                }, this);
              dialog.open();
              
            }, this);
          return(item);
        },

        bindItem : function(controller, item, id) {
          controller.bindProperty("title", "title", null, item, id);
          controller.bindProperty("dn", "dn", null, item, id);
          controller.bindProperty("uuid", "uuid", null, item, id);
          controller.bindProperty("description", "description", null, item, id);
          controller.bindProperty("icon", "icon", null, item, id);
          controller.bindProperty("", "model", null, item, id);
        },

        filter : function(data) {
          var show = true;

          if (that.__selection['secondary'] != "enabled") {
            show = data.getSecondary() == false;
          }

          if (show && that.__selection['category'] != 'all' && that.__selection['category'] != data.getType()) {
            show = false;
          }

          if (show && that.__selection['mod-time'] != 'all') {
            show = data.getLastChanged().toTimeStamp() > (that.__now - deltas[that.__selection['mod-time']]);
          }

          return show;
        }
      });

    this.resultList.getPane().getRowConfig().setDefaultItemSize(80);

    // Establish a timer that handles search updates
    var timer = qx.util.TimerManager.getInstance();
    this.sf.addListener("focusin", function() {
      if (!this._timer) {
        this._timer = timer.start(this._search_queue_handler, 500, this, null, 2000);
      }
    }, this);
    this.sf.addListener("focusout", function() {
      timer.stop(this._timer);
      this._timer = null; 
    }, this);

    // Focus search field
    this.sf.addListener("appear", this.updateFocus, this);
    this._removedObjects = [];
    this._createdObjects = [];
    this._modifiedObjects = [];
    this._currentResult = [];

    // Listen for object changes comming from the backend
    gosa.io.Sse.getInstance().addListener("objectModified", this._handleObjectEvent, this);
    gosa.io.Sse.getInstance().addListener("objectCreated", this._handleObjectEvent, this);
    gosa.io.Sse.getInstance().addListener("objectRemoved", this._handleObjectEvent, this);
  },

  events: {
    "loadingComplete" : "qx.event.type.Data"
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */

  members :
  {
    // The timestamp of the last event that triggered a list reload
    _lastUpdateReload: null,

    _sq : null,
    _timer : null,
    _working : false,
    _old_query : "",

    _removedObjects: null,
    _createdObjects: null,
    _modifiedObjects: null,
    _currentResult: null,
    __selection: null,
    __default_selection: null,
    __now: null,

    
    updateFocus: function(){
      var _self = this;
      setTimeout(function() {
          _self.sf.focus();
        });
    },

    _search_queue_handler : function() {
      if (this._sq.length == 0 || this._working) {
        return;
      }

      // Lock us
      this._working = true;

      // Do search and lock ourselves
      this.doSearch(null, function() {
        this._working = false;
      });
    },

    _handle_key_event : function(e) {
      // Push the search to the search queue
      if (this.sf.getValue().length > 2) {
        this._sq.push(this.sf.getValue());
      }
    },

    updateFilter : function(e) {
      var d = new Date();
      this.__selection = this.searchAid.getSelection();
      this.__now = d.getTime() / 1000 + d.getTimezoneOffset() * 60;
      this.resultList.refresh();
    },

    doSearchE : function(e, callback, noListUpdate) {
      this._sq.push(this.sf.getValue());
      this.doSearch(e, callback, noListUpdate);
    },

    doSearch : function(e, callback, noListUpdate) {

      // Remove all entries from the queue and keep the newest
      var query = "";
      while (true) {
         var _query = this._sq.shift();
         if (!_query) {
           break;
         }
         query = _query;
      }
     
      // Don't search for nothing or not changed values
      if (!noListUpdate && (query == "" || this._old_query == query)) {
        if (callback) {
          callback.apply(this, [ [] ]);
        }
        return;
      }
      
      var rpc = gosa.io.Rpc.getInstance();
      var base = gosa.Session.getInstance().getBase();
      var startTime = new Date().getTime();

      // Try ordinary search
      rpc.cA(function(result, error){

          if(error){
            var d = new gosa.ui.dialogs.Error(this.tr("Insufficient permission!"));
            d.open();
          }else{
            var endTime = new Date().getTime();

            // Memorize old query and display results
            if(!noListUpdate){
              this.showSearchResults(result, endTime - startTime, false, query);
              this._old_query = query;
            }

            if (callback) {
              callback.apply(this, [result, endTime - startTime]);
            }
          }
        }, this, "search", base, "sub", query, this.__default_selection);
    },

    showSearchResults : function(items, duration, fuzzy, query) {
      var i = items.length;

      this._currentResult = items;

      this.searchInfo.show();
      this.resultList.getChildControl("scrollbar-x").setPosition(0);
      this.resultList.getChildControl("scrollbar-y").setPosition(0);

      if (i == 0){
          this.searchResult.hide();
      } else {
          this.searchResult.show();
      }

      var d = Math.round(duration / 10) / 100;
      if (fuzzy) {
          this.sii.setValue(this.trn("%1 fuzzy result", "%1 fuzzy results", i, i) + " / " + this.tr("no exact matches") + " (" + this.trn("%1 second", "%1 seconds", d, d) + ")");
      } else {
          this.sii.setValue(this.trn("%1 result", "%1 results", i, i) + " (" + this.trn("%1 second", "%1 seconds", d, d) + ")");
      }

      var model = [];
      var _categories = {};

      // Build model
      var tmp = this.searchAid.getSelection();
      if (tmp['category']) {
        this.__selection = tmp;
      }


      for (var i= 0; i<items.length; i++) {
        var item = new gosa.data.model.SearchResultItem();
        item = this.__fillSearchListItem(item, items[i]);
        model.push(item);
        
        // Update categories
        if (!_categories[items[i]['tag']]) {
            _categories[items[i]['tag']] = this['tr'](gosa.Cache.object_categories[items[i]['tag']]);
        }
      }

      // Memorize categories
      this._categories = _categories;

      // Pseudo sort categories
      var categories = {"all" : this.tr("All")};
      var tmp = [];
      for (var i in _categories) {
        tmp.push([i, _categories[i]]);
      }
      tmp.sort(function(a, b) {
        a = a[1];
        b = b[1];
        return a < b ? -1 : (a > b ? 1 : 0);
      });
      for (var i=0; i<tmp.length; i++) {
        categories[tmp[i][0]] = tmp[i][1];
      }

      // Update model
      var data = new qx.data.Array(model);
      data.sort(this.__sortByRelevance);
      this.resultList.setModel(data);
      
      // Update categories
      if (this.searchAid.hasFilter()) {
        this.searchAid.updateFilter("category", categories);

      } else {

        this.searchAid.addFilter(this.tr("Category"), "category",
            categories, this.__selection['category']);

        this.searchAid.addFilter(this.tr("Secondary search"), "secondary", {
            "enabled": this.tr("Enabled"),
            "disabled": this.tr("Disabled")
        }, this.__selection['secondary']);

        this.searchAid.addFilter(this.tr("Last modification"), "mod-time", {
            "all": this.tr("All"),
            "hour": this.tr("Last hour"),
            "day": this.tr("Last 24 hours"),
            "week": this.tr("Last week"),
            "month": this.tr("Last month"),
            "year": this.tr("Last year")
        }, this.__selection['mod-time']);
      }
    },

    __sortByRelevance: function(a, b){
      if (a.getRelevance() == b.getRelevance()) {
        return 0;
      }
      if (a.getRelevance() < b.getRelevance()) {
        return -1;
      }
      return 1;
    },

    /* Highlights query strings in the given string
     * */
    _highlight : function(string, query) {
        var reg = new RegExp('(' + qx.lang.String.escapeRegexpChars(query) + ')', "ig");
        return string.replace(reg, "<b>$1</b>");
    },

    /* Removes the object given by its uuid
     * */
    removeObject: function(uuid){
      var rpc = gosa.io.Rpc.getInstance();
      rpc.cA(function(result, error){
          if(error){
            new gosa.ui.dialogs.Error(this.tr("Cannot remove entry!")).open();
            this.error("cannot remove entry: " + error);
          }
        }, this, "removeObject", "object", uuid); 
    },

    /* Open the object given by its uuid/dn
     * */
    openObject : function(dn) {
      var win = null;

      gosa.proxy.ObjectFactory.openObject(function(obj, error){

        // Check for errors
        if(error){
          new gosa.ui.dialogs.Error(error.message).open();
          this.fireDataEvent("loadingComplete", {dn: dn});
          return;
        }

        // Build widget and place it into a window
        gosa.ui.Renderer.getWidget(function(w){
          var doc = qx.core.Init.getApplication().getRoot();
          win = new qx.ui.window.Window(this.tr("Object") + ": " + obj.dn);
          win.setWidth(800);
          win.setLayout(new qx.ui.layout.Canvas());
          win.add(w, {top: 0, bottom: 0, left: 0, right: 0});
          win.addListener("appear", win.center, win);
          win.open();

          // See http://bugzilla.qooxdoo.org/show_bug.cgi?id=1770
          win.setShowMinimize(false);

          w.addListener("done", function(){
            w.dispose();
            doc.remove(win);
            win.destroy();
          }, this);

          win.addListener("close", function(){
            w.dispose();
            doc.remove(win);
            obj.close();
            win.destroy();
          }, this);

          // Position window as requested
          doc.add(win);

          this.fireDataEvent("loadingComplete", {dn: dn});

        }, this, obj);
      }, this, dn);
    },


    /* Act on object modification events
     * */

    /* Act on backend events related to object modifications
     * and remove, update or add list item of the result list.
     *
     * */
    _handleObjectEvent: function(e){

      // Keep track of each event uuid we receive
      var data = e.getData();
      if(data['changeType'] == "remove"){
        this._removedObjects.push(data['uuid']);
      }
      if(data['changeType'] == "create"){
        this._createdObjects.push(data['uuid']);
      }
      if(data['changeType'] == "update"){
        this._modifiedObjects.push(data['uuid']);
      }

      //console.log("ADD: ", this._createdObjects);
      //console.log("DEL: ", this._removedObjects);
      //console.log("MOD: ", this._modifiedObjects);

      // Once an event was catched, start a new query, but do not show
      // the result in the list, instead just return it.
      this.doSearchE(null, function(result){
      
          // Check for differences between the currently active result-set 
          // and the fetched one.
          var added = [];
          var removed = [];
          var stillthere = [];
          var entries_by_uuid = {};

          // Create a list containing all currently show entry-uuids.
          var current_uuids = [];
          for(var i=0; i<this._currentResult.length; i++){
            current_uuids.push(this._currentResult[i]['uuid']);
            entries_by_uuid[this._currentResult[i]['uuid']] = this._currentResult[i];
          }

          // Create  list of all entry-uuids that ware returned by the query.
          var uuids = [];
          for(var i=0; i<result.length; i++){
            uuids.push(result[i]['uuid']);
            entries_by_uuid[result[i]['uuid']] = result[i];
          }

          // Check which uuids were new, which were removed and which uuids are still there
          removed = qx.lang.Array.exclude(qx.lang.Array.clone(current_uuids), uuids);
          added = qx.lang.Array.exclude(qx.lang.Array.clone(uuids), current_uuids);
          stillthere = qx.lang.Array.exclude(current_uuids, added);
          stillthere = qx.lang.Array.exclude(stillthere, removed);

          //console.log("added", added);
          //console.log("removed", removed);
          //console.log("stillthere", stillthere);

          // Walk through collected "remove-event" uuids and check if they were in our list
          // before, but are now gone. If so, then fade it out.
          // If its no longer in our list, but was not removed before (e.g just moved) then
          // just remove it from the list without fading it out.
          for(var i=0; i<removed.length; i++){
            if(qx.lang.Array.contains(this._removedObjects, removed[i])){
              this.__fadeOut(entries_by_uuid[removed[i]]);
            }else{
              this.__removeEntry(entries_by_uuid[removed[i]]);
            }
            this.updateFilter();
            qx.lang.Array.remove(this._removedObjects, removed[i]);
          }

          // Walk through all uuids that were there before and are still there.
          // If there was an modify event for one of the uuids, then update
          // the list entry.
          for(var i=0; i<stillthere.length; i++){
            if(qx.lang.Array.contains(this._modifiedObjects, stillthere[i])){
              this.__updateEntry(entries_by_uuid[stillthere[i]]);
              this.updateFilter();
            }
            qx.lang.Array.remove(this._modifiedObjects, stillthere[i]);
          }

          // If there is a new entry in the result and we've got an create event
          // then fade the new entry in the result list.
          for(var i=0; i<added.length; i++){
            if(qx.lang.Array.contains(this._createdObjects, added[i])){
              this.__fadeIn(entries_by_uuid[added[i]]);
            }else{
              this.__addEntry(entries_by_uuid[added[i]]);
            }
            this.updateFilter();
            qx.lang.Array.remove(this._createdObjects, added[i]);
          }
        }, true);
    },


    /* Update the given result-list item of the search-result-list
     * and reload the model.
     * */
    __updateEntry: function(entry){

      // Locate the search result item in the search result model
      // and update it.
      var model = this.resultList.getModel();
      for(var i=0; i<model.getLength(); i++){
        if(entry['uuid'] == model.getItem(i).getUuid()){
          var item = model.getItem(i);
          item = this.__fillSearchListItem(item, entry);
          model.setItem(i, item);
          this.resultList.setModel(model);
          break;
        }
      }

      // Now remove the entry from the current result set
      for(var i=0; i<this._currentResult.length; i++){
        if(this._currentResult[i]['uuid'] == entry['uuid']){
          this._currentResult[i] = entry;
          return;
        }
      }
    },


    /* Adds a new entry to the search result-model
     * */
    __addEntry: function(entry){

      // Add the given result-item to the list
      // and update the model
      var model = this.resultList.getModel();
      var item = new gosa.data.model.SearchResultItem();
      item = this.__fillSearchListItem(item, entry);
      model.push(item);
      model.sort(this.__sortByRelevance);
      this.resultList.setModel(model);

      // Also add this result-item to the current result set,
      // else we would add the item the the result-list
      // again and again and ...
      this._currentResult.push(entry);
      return;
    },


    /* Removes the given search-result entry from the result-list
     * and updates the model.
     * */
    __removeEntry: function(entry){

      // Locate the model entry with the given uuid
      // and then remove it from the model.
      var model = this.resultList.getModel();
      for(var i=0; i<model.getLength(); i++){
        if(entry['uuid'] == model.getItem(i).getUuid()){
          qx.lang.Array.remove(model, model.getItem(i));
          this.resultList.setModel(model);
          break;
        }
      }

      // Now remove the entry from the current result set.
      for(var i=0; i<this._currentResult.length; i++){
        if(this._currentResult[i]['uuid'] == entry['uuid']){
          qx.lang.Array.remove(this._currentResult, this._currentResult[i]);
          return;
        }
      }
      return;
    },


    /* Returns the model item for a given uuid
     * */
    __getModelEntryForUUID: function(uuid){
      var model = this.resultList.getModel();
      for(var i=0; i<model.getLength();i++){
        if(model.getItem(i).getUuid() == uuid){
          return(model.getItem(i));
        }
      }
      return(null);
    },


    /* Fades out the given search-result entry and finally
     * removes it.
     * */
    __fadeOut: function(entry){
      this.__removeEntry(entry);
    },


    /* Adds the given search result entry to the list 
     * and then starts a fade-in transition for it.
     * */
    __fadeIn: function(entry){
      this.__addEntry(entry);
    },


    /* Updates the properties of an 'gosa.data.model.SearchResultItem' using
     * the given search-result-entry.
     * */
    __fillSearchListItem: function(item, entry){

      // Set the uuid first, this triggers a reset on the widget side.
      item.setUuid(entry['uuid']);

      // Icon fallback to server provided images
      var icon = entry['icon'];
      if (!icon) {
          icon = gosa.Config.spath + "/resources/images/objects/64/" + entry['tag'].toLowerCase() + ".png";
      }

      item.setDn(entry['dn']);
      item.setTitle(entry['title']);
      item.setLastChanged(entry['lastChanged']);
      item.setRelevance(entry['relevance']);
      item.setSecondary(entry['secondary']);
      item.setType(entry['tag']);
      item.setDescription(this._highlight(entry['description'], this._old_query));
      item.setIcon(icon);
      return(item); 
    }
  }
});
