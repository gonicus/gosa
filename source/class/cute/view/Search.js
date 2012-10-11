/* ************************************************************************

   Copyright: 2012, GONICUS GmbH

   License:

   Authors: Cajus Pollmeier <pollmeier@gonicus.de>
            Fabian Hickert <hickert@gonicus.de>

************************************************************************ */

/* ************************************************************************

#asset(cute/*)

************************************************************************ */

qx.Class.define("cute.view.Search",
{
  extend : qx.ui.tabview.Page,

  construct : function()
  {
    this._sq = [];
    var barWidth = 200;

    // Default search parameters
    this.__default_selection = {
        'fallback': true,
        'secondary': "enabled",
        'category': "all",
        'mod-time': "all"
    };
    this._categories = {};

    // Call super class and configure ourselfs
    this.base(arguments, "", cute.Config.getImagePath("apps/search.png", 32));
    this._excludeChildControl("label");
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
    this.searchAid = new cute.ui.SearchAid();
    this.searchAid.setWidth(barWidth);
    this.searchResult.add(this.searchAid, {left: 0, bottom: 0, top: 0});
    this.searchAid.addListener("filterChanged", this.updateFilter, this);

    this.add(this.searchResult, {flex: 1});

    // Bind search methods
    sb.addListener("execute", this.doSearchE, this);
    sf.addListener("keyup", this._handle_key_event, this);
    this.sf = sf;

    // Bind search result model
    var that = this;
    this.resultList.setDelegate({
        createItem: function(){

          var item = new cute.ui.SearchListItem();
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
              var dialog = new cute.ui.dialogs.RemoveObject(e.getData().getDn());
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
    var _self = this;
    setTimeout(function() {
      _self.sf.focus();
    });
    this.sf.focus();

    this._removedObjects = [];
    this._createdObjects = [];
    this._modifiedObjects = [];
    this._currentResult = [];

    // Listen for object changes comming from the backend
    cute.io.WebSocket.getInstance().addListener("objectModified", this._handleObjectEvent, this);
    cute.io.WebSocket.getInstance().addListener("objectCreated", this._handleObjectEvent, this);
    cute.io.WebSocket.getInstance().addListener("objectRemoved", this._handleObjectEvent, this);
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
    _old_query : null,

    _removedObjects: null,
    _createdObjects: null,
    _modifiedObjects: null,
    _currentResult: null,


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
      var selection = this.searchAid.getSelection();
      console.error("----> change filter model is missing");
      console.log(e);
      console.log(e.getUserData());
    },

    doSearchE : function(e, callback, noListUpdate) {
      this._sq.push(this.sf.getValue());
      this.doSearch(e, callback, noListUpdate);
    },

    doSearch : function(e, callback, noListUpdate) {

      // Remove all entries from the queue and keep the newest
      var query = "";
      while (true) {
         var q = this._sq.shift();
         if (!q) {
           break;
         }
         query = q;
      }
     
      // Don't search for nothing or not changed values
      if (!noListUpdate && (query == "" || this._old_query == query)) {
        if (callback) {
          callback.apply(this, [ [] ]);
        }
        return;
      }
      
      var rpc = cute.io.Rpc.getInstance();
      rpc.cA(function(result, error){
        if(!error){
          var base = result;
          var startTime = new Date().getTime();

          // Try ordinary search
          rpc.cA(function(result, error){
            var endTime = new Date().getTime();

            // Memorize old query and display results
            if(!noListUpdate){
              this.showSearchResults(result, endTime - startTime, false, query);
            }
            this._old_query = query;

            if (callback) {
              callback.apply(this, [result, endTime - startTime]);
            }
          }, this, "search", base, "sub", query, this.__default_selection);
        }
      }, this, "getBase");
    },

    showSearchResults : function(items, duration, fuzzy, query) {
      var i = items.length;

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
      for (var i= 0; i<items.length; i++) {
        var item = new cute.data.model.SearchResultItem();

        // Icon fallback to server provided images
        var icon = items[i]['icon'];
        if (!icon) {
            icon = cute.Config.spath + "/" + cute.Config.getTheme() + "/resources/images/objects/" + items[i]['tag'].toLowerCase() + ".png";
        }

        item.setUuid(items[i]['uuid']);
        item.setDn(items[i]['dn']);
        item.setTitle(items[i]['title']);
        item.setRelevance(items[i]['relevance']);
        item.setType(items[i]['tag']);
        item.setDescription(this._highlight(items[i]['description'], query));
        item.setIcon(icon);
        model.push(item);
        
        // Update categories
        if (!_categories[items[i]['tag']]) {
          _categories[items[i]['tag']] = this.tr(items[i]['tag']);
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
            categories, this.__default_selection['category']);

        this.searchAid.addFilter(this.tr("Secondary search"), "secondary", {
            "enabled": this.tr("Enabled"),
            "disabled": this.tr("Disabled")
        }, this.__default_selection['secondary']);

        this.searchAid.addFilter(this.tr("Last modification"), "mod-time", {
            "all": this.tr("All"),
            "hour": this.tr("Last hour"),
            "day": this.tr("Last 24 hours"),
            "week": this.tr("Last week"),
            "month": this.tr("Last month"),
            "year": this.tr("Last year")
        }, this.__default_selection['mod-time']);
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
      var rpc = cute.io.Rpc.getInstance();
      rpc.cA(function(result, error){
          if(error){
            new cute.ui.dialogs.Error(this.tr("Failed to remove the entry!") + " " + error.message).open();
          }
        }, this, "removeObject", "object", uuid); 
    },

    /* Open the object given by its uuid/dn
     * */
    openObject : function(dn) {
      var win = null;

      cute.proxy.ObjectFactory.openObject(function(obj, error){

        // Check for errors
        if(error){
          new cute.ui.dialogs.Error(error.message).open();
          this.fireDataEvent("loadingComplete", {dn: dn});
          return;
        }

        // Build widget and place it into a window
        cute.ui.Renderer.getWidget(function(w){
          var doc = qx.core.Init.getApplication().getRoot();
          win = new qx.ui.window.Window(this.tr("Object") + ": " + obj.dn);
          win.setLayout(new qx.ui.layout.VBox(10));
          win.setWidth(800);
          win.add(w);
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
     * */
    _handleObjectEvent: function(e){

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

      this.doSearchE(null, function(result){
      
          var added = [];
          var removed = [];
          var stillthere = [];
          var entries_by_uuid = {};

          var current_uuids = [];
          for(var i=0; i<this._currentResult.length; i++){
            current_uuids.push(this._currentResult[i]['uuid']);
            entries_by_uuid[this._currentResult[i]['uuid']] = this._currentResult[i];
          }

          var uuids = [];
          for(var i=0; i<result.length; i++){
            uuids.push(result[i]['uuid']);
            entries_by_uuid[result[i]['uuid']] = result[i];
          }

          removed = qx.lang.Array.exclude(qx.lang.Array.clone(current_uuids), uuids);
          added = qx.lang.Array.exclude(qx.lang.Array.clone(uuids), current_uuids);

          stillthere = qx.lang.Array.exclude(current_uuids, added);
          stillthere = qx.lang.Array.exclude(stillthere, removed);

          for(var i=0; i<removed.length; i++){
            if(qx.lang.Array.contains(this._removedObjects, removed[i])){
              this.__fadeOut(entries_by_uuid[removed[i]]);
            }else{
              this.__removeEntry(entries_by_uuid[removed[i]]);
            }
            qx.lang.Array.remove(this._removedObjects, removed[i]);
          }
          for(var i=0; i<stillthere.length; i++){
            if(qx.lang.Array.contains(this._modifiedObjects, stillthere[i])){
              this.__updateEntry(entries_by_uuid[stillthere[i]]);
            }
            qx.lang.Array.remove(this._modifiedObjects, stillthere[i]);
          }
          for(var i=0; i<added.length; i++){
            if(qx.lang.Array.contains(this._createdObjects, added[i])){
              this.__addEntry(entries_by_uuid[added[i]]);
            }
            qx.lang.Array.remove(this._createdObjects, added[i]);
          }
        }, true);
    },

    __updateEntry: function(entry){
    
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


    __addEntry: function(entry){
      var model = this.resultList.getModel();
      var item = new cute.data.model.SearchResultItem();
      item = this.__fillSearchListItem(item, entry);
      model.push(item);
      model.sort(this.__sortByRelevance);
      this.resultList.setModel(model);
      this._currentResult.push(entry);
      return;
    },

    __removeEntry: function(entry){
      var model = this.resultList.getModel();
      for(var i=0; i<model.getLength(); i++){
        if(entry['uuid'] == model.getItem(i).getUuid()){
          qx.lang.Array.remove(model, model.getItem(i));
          this.resultList.setModel(model);
          break;
        }
      }

      // Now remove the entry from the current result set
      for(var i=0; i<this._currentResult.length; i++){
        if(this._currentResult[i]['uuid'] == entry['uuid']){
          qx.lang.Array.remove(this._currentResult, this._currentResult[i]);
          return;
        }
      }
      return;
    },

    __fillSearchListItem: function(item, entry){

      // Icon fallback to server provided images
      var icon = entry['icon'];
      if (!icon) {
          icon = cute.Config.spath + "/" + cute.Config.getTheme() + "/resources/images/objects/" + entry['tag'].toLowerCase() + ".png";
      }

      item.setUuid(entry['uuid']);
      item.setDn(entry['dn']);
      item.setTitle(entry['title']);
      item.setRelevance(entry['relevance']);
      item.setType(entry['tag']);
      item.setDescription(this._highlight(entry['description'], this._old_query));
      item.setIcon(icon);
      return(item); 
    },

    __fadeOut: function(entry){
      this.__removeEntry(entry);
    }
  }
});
