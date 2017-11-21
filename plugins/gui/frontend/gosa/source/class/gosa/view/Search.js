/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

/* ************************************************************************

#asset(gosa/*)

************************************************************************ */

qx.Class.define("gosa.view.Search", {
  extend : qx.ui.tabview.Page,
  type: "singleton",

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
    this.base(arguments, "", "@Ligature/search");
    this.getChildControl("button").getChildControl("label").exclude();
    this.setLayout(new qx.ui.layout.VBox(5));

    // Create search field / button
    var searchHeader = this._searchHeader = new qx.ui.container.Composite();
    var searchLayout = new qx.ui.layout.HBox(10);
    searchHeader.setLayout(searchLayout);

    var sf = this.searchField = new qx.ui.form.TextField('');
    sf.setPlaceholder(this.tr("Please enter your search..."));
    this.addListener("resize", function() {
      var newWidth = parseInt(this.getBounds().width / 2);
      sf.setWidth(newWidth);
      searchHeader.setUserBounds(0, 35, this.getBounds().width, 34);

      if (this._alreadyVisible && this._delta) {
        this._delta = parseInt(this.getBounds().height / 3) - 35;
        qx.bom.element.Animation.animate(this._searchHeader.getContentElement().getDomElement(), {
          duration: 0, keep: 100, keyFrames: { 0: { "translate": ["0px", "0px"] }, 100: { "translate" : ["0px", this._delta + "px"]}}
        });
      }
    }, this);
    searchHeader.add(sf);

    searchHeader.addListenerOnce("appear", function() {
      this._alreadyVisible = true;
      this._delta = parseInt(this.getBounds().height / 3) - 35;
      qx.bom.element.Animation.animate(this._searchHeader.getContentElement().getDomElement(), {
        duration: 0, keep: 100, keyFrames: { 0: { "translate": ["0px", "0px"] }, 100: { "translate" : ["0px", this._delta + "px"]}}
      });
    }, this);

    var sb = new qx.ui.form.Button(this.tr("Search"));
    sb.setAppearance("button-primary");
    searchHeader.add(sb);

    searchLayout.setAlignX("center");

    this.add(searchHeader);

    this._spinner = new gosa.ui.Throbber();
    this._spinner.exclude();
    this._spinner.setMarginTop(200);
    this.add(this._spinner, {flex: 1});

    // Create search info (hidden)
    this.searchInfo = new qx.ui.container.Composite(new qx.ui.layout.HBox(10));
    this.searchInfo.hide();
    this.searchInfo.setMarginTop(70);
    this.searchInfo.setPadding(20);
    var sil = new qx.ui.basic.Label(this.tr("Search"));
    sil.setTextColor("bittersweet-dark");
    sil.setFont(qx.bom.Font.fromString("20px Sans Serif"));
    sil.setWidth(barWidth);
    this.searchInfo.add(sil);

    this.sii = new qx.ui.basic.Label();
    this.sii.set({
      textColor: "darkgray-light",
      alignY: "bottom",
      rich: true,
      wrap: true
    });
    this.searchInfo.add(this.sii);

    this.add(this.searchInfo);

    // Create search result
    this.searchResult = new qx.ui.container.Composite(new qx.ui.layout.Canvas());
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
    var deltas = {'hour': 60*60, 'day': 60*60*24 , 'week': 60*60*24*7, 'month': 2678400, 'year': 31536000};
    this.resultList.setDelegate({
        createItem: function() {

          var item = new gosa.ui.SearchListItem();
          item.addListener("edit", function(e){
              item.setIsLoading(true);
              gosa.ui.controller.Objects.getInstance().openObject(e.getData().getDn())
              .finally(function() {
                item.setIsLoading(false);
              });
            }, this);

          item.addListener("remove", function(e){
              var dialog = new gosa.ui.dialogs.RemoveObject(e.getData().getDn());
              dialog.addListener("remove", function(){
                gosa.proxy.ObjectFactory.removeObject(item.getUuid());
              });
              dialog.open();

            }, this);
          return(item);
        }.bind(this),

        bindItem : function(controller, item, id) {
          controller.bindProperty("title", "title", null, item, id);
          controller.bindProperty("type", "type", null, item, id);
          controller.bindProperty("dn", "dn", null, item, id);
          controller.bindProperty("uuid", "uuid", null, item, id);
          controller.bindProperty("description", "description", null, item, id);
          controller.bindProperty("icon", "icon", null, item, id);
          controller.bindProperty("", "model", null, item, id);
        },

        sorter: this.__sortByRelevance,

        filter : function(data) {
          var show = true;

          if (this.__selection.secondary && this.__selection.secondary !== "enabled") {
            show = data.getSecondary() === false;
          }

          if (show && this.__selection.category && this.__selection.category !== 'all' && this.__selection.category != data.getType()) {
            show = false;
          }

          if (show && this.__selection["mod-time"] && this.__selection["mod-time"] !== 'all') {
            show = data.getLastChanged().toTimeStamp() > (this.__now - deltas[this.__selection["mod-time"]]);
          }

          return show;
        }.bind(this)
      });

    this.resultList.getPane().getRowConfig().setDefaultItemSize(80);

    // Focus search field
    this.sf.addListener("appear", this.updateFocus, this);
    this._removedObjects = [];
    this._createdObjects = [];
    this._modifiedObjects = [];
    this._currentResponse = {};

    // Listen for object changes coming from the backend
    this.__debouncedReload = qx.util.Function.debounce(this._handleObjectEvent, 500, true);
    gosa.io.Sse.getInstance().addListener("objectModified", this.__debouncedReload, this);
    gosa.io.Sse.getInstance().addListener("objectCreated", this.__debouncedReload, this);
    gosa.io.Sse.getInstance().addListener("objectRemoved", this.__debouncedReload, this);
    gosa.io.Sse.getInstance().addListener("objectMoved", this.__debouncedReload, this);
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    appearance: {
      refine: true,
      init: "gosa-tabview-page"
    },

    // if true every filter update triggers a new search
    searchOnFilterUpdate: {
      check: "Boolean",
      init: false
    }
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

    _alreadyVisible : false,
    _delta : 0,
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
    __searchPromise : null,
    __fuzzy: null,
    __duration: null,
    __debouncedReload: null,


    updateFocus: function(){
      var _self = this;
      setTimeout(function() {
          _self.sf.focus();
        });
    },

    _handle_key_event : function(e) {
      // Push the search to the search queue
      if (this.sf.getValue().length > 2) {
        this.doSearchE();

        if (this._delta) {
          qx.bom.element.Animation.animate(this._searchHeader.getContentElement().getDomElement(), {
            timing : "ease-in-out",
            duration : 250,
            keep : 100,
            keyFrames : {
              0 : {
                "translate" : ["0px", this._delta + "px"]
              },
              100 : {
                "translate" : ["0px", "0px"]
              }
            }
          });
  
          this._delta = 0;
        }

      }
    },

    updateFilter : function(ev) {
      if (ev && (ev.getData().triggerSearch || (this.__selection.secondary === "disabled" && this.searchAid.getSelection().secondary === "enabled"))) {
        // search again as we need secondary results also
        this.__selection = qx.lang.Object.mergeWith(this.__default_selection, this.searchAid.getSelection());
        this.doSearch(false, true);
      } else {
        var d = new Date();
        this.__selection = this.searchAid.getSelection();

        this.__now = d.getTime() / 1000 + d.getTimezoneOffset() * 60;
        this.resultList.refresh();
        this.__updateResultInfo(this.resultList.getPane().getRowConfig().getItemCount());
      }
    },

    showSpinner: function() {
      this.searchResult.hide();
      this.searchInfo.hide();
      this._spinner.show();
    },

    hideSpinner: function() {
      this._spinner.exclude();
      this.searchInfo.show();
    },

    doSearchE : qx.util.Function.debounce(function(noListUpdate) {
      return this.doSearch(noListUpdate);
    }, 200, false),

    doSearch : function(noListUpdate, selection) {
      console.time('search');
      var query = this.sf.getValue();

      // Don't search for nothing or not changed values
      if (!noListUpdate && !selection && (query === "" || this._old_query === query)) {
        return qx.Promise.resolve([]);
      }
      if (!noListUpdate) {
        this.showSpinner();
      }
      if (!selection) {
        selection = this.__selection = this.__default_selection;
      }

      var rpc = gosa.io.Rpc.getInstance();
      var base = gosa.Session.getInstance().getBase();
      var startTime = new Date().getTime();

      // Try ordinary search
      if (this.__searchPromise) {
        this.__searchPromise.cancel();
      }
      console.time('search RPC');
      this._old_query = query;
      return this.__searchPromise = rpc.cA("search", base, "sub", query, selection)
      .then(function(result) {
        console.timeEnd('search RPC');
        var endTime = new Date().getTime();

        // Memorize old query and display results
        if(!noListUpdate) {
          this.showSearchResults(result, endTime - startTime, !!selection.fallback, query);
        }

        return result;
      }, this)
      .catch(function(error) {
        this.error(error);
        var d = new gosa.ui.dialogs.Error(error);
        d.open();
        this._old_query = null;
      }, this)
      .finally(function() {
        if (!noListUpdate && !this.isDisposed()) {
          this.hideSpinner();
        }
        console.timeEnd('search');
      }, this);

    },

    __updateResultInfo: function(count) {
      var resultString = "";
      var isFuzzy = this._currentResponse.hasOwnProperty("fuzzy") && !!this._currentResponse.fuzzy;
      var moreResults= this._currentResponse.total > this._currentResponse.results.length;

      if (isFuzzy) {
        resultString += this.tr("Search for '%1' returned no results, searched for '%2' instead", this._currentResponse.orig, this._currentResponse.fuzzy)+"<br/><br/>";
      }
      if (moreResults) {
        resultString += this.trn("%1 / %2 result shown", "%1 / %2 results shown", count, count, this._total);
      } else {
        resultString += this.trn("%1 result", "%1 results", count, count);
      }
      resultString += " (" + this.trn("%1 second", "%1 seconds", this.__duration, this.__duration) + ")";
      if (moreResults) {
        resultString += "<br>"+this.tr("Please consider using a more specific search string or filters to reduce the result set. ");
      }
      this.sii.setValue(resultString);
    },

    showSearchResults : function(result, duration, fuzzy, query) {
      this._currentResponse = result;
      var items = result.results;
      this._total = result.total;
      var i = items.length;

      this.searchInfo.show();
      this.resultList.getChildControl("scrollbar-x").setPosition(0);
      this.resultList.getChildControl("scrollbar-y").setPosition(0);

      if (i === 0){
          this.searchResult.hide();
      } else {
          this.searchResult.show();
      }
      this.__duration = Math.round(duration / 10) / 100;
      this.__fuzzy = fuzzy;
      this.__updateResultInfo(i);
      this.setSearchOnFilterUpdate(i < this._total);

      var model = [];
      var _categories = {};

      // Build model
      var tmp = this.searchAid.getSelection();
      if (tmp.category) {
        this.__selection = tmp;
      }

      var secondaryCount = 0;
      var modifiedCounters = {
        "hour" : 0,
        "day": 0,
        "week": 0,
        "month": 0,
        "year": 0
      };
      for (i = 0; i<items.length; i++) {
        var item = new gosa.data.model.SearchResultItem();
        item = this.__fillSearchListItem(item, items[i]);
        model.push(item);

        var modifiedDelta = this.__now - item.getLastChanged().toTimeStamp();
        if (modifiedDelta <= 3600) {
          modifiedCounters.hour++;
          modifiedCounters.day++;
          modifiedCounters.week++;
          modifiedCounters.month++;
          modifiedCounters.year++;
        } else if (modifiedDelta <= 3600*24) {
          modifiedCounters.day++;
          modifiedCounters.week++;
          modifiedCounters.month++;
          modifiedCounters.year++;
        } else if (modifiedDelta <= 3600*24*7) {
          modifiedCounters.week++;
          modifiedCounters.month++;
          modifiedCounters.year++;
        } else if (modifiedDelta <= 3600*24*7*31) {
          modifiedCounters.month++;
          modifiedCounters.year++;
        } else if (modifiedDelta <= 3600*24*7*365) {
          modifiedCounters.year++;
        }

        // Update categories
        if (!_categories[items[i].tag]) {
          if (gosa.Cache.objectCategories[items[i].tag]) {
            _categories[items[i].tag] = {
              name: this["tr"](gosa.Cache.objectCategories[items[i].tag]),
              count: 1
            };  // jshint ignore:line
          }
        } else {
          _categories[items[i].tag].count++;
        }

        if (items[i].secondary === true) {
          secondaryCount++;
        }
      }

      // Memorize categories
      this._categories = _categories;

      // Pseudo sort categories
      var categories = {"all" : {
        name : this.tr("All"),
        count: items.length
      }
      };
      tmp = [];
      for (i in _categories) {
        tmp.push([i, _categories[i]]);
      }
      tmp.sort(function(a, b) {
        a = a[1].name;
        b = b[1].name;
        return a < b ? -1 : (a > b ? 1 : 0);
      });
      for (i = 0; i<tmp.length; i++) {
        categories[tmp[i][0]] = tmp[i][1];
      }

      // Update model
      var data = new qx.data.Array(model);
      this.resultList.setModel(data);

      // Update categories
      if (this.searchAid.hasFilter()) {
        this.searchAid.updateFilter("category", categories);
        this.searchAid.updateFilter("secondary", {
          "enabled": { name: this.tr("Enabled"), count: items.length },
          "disabled": { name: this.tr("Disabled"), count: (items.length - secondaryCount) }
        });
        this.searchAid.updateFilter("mod-time", {
          "all": { name: this.tr("All"), count: items.length },
          "hour": { name: this.tr("Last hour"), count: modifiedCounters.hour },
          "day": { name: this.tr("Last 24 hours"), count: modifiedCounters.day },
          "week": { name: this.tr("Last week"), count: modifiedCounters.week },
          "month": { name: this.tr("Last month"), count: modifiedCounters.month },
          "year": { name: this.tr("Last year"), count: modifiedCounters.year }
        });
      } else {
        this.searchAid.addFilter(this.tr("Category"), "category",
            categories, this.__selection.category);

        this.searchAid.addFilter(this.tr("Secondary search"), "secondary", {
            "enabled": { name: this.tr("Enabled"), count: items.length },
            "disabled": { name: this.tr("Disabled"), count: (items.length - secondaryCount) }
        }, this.__selection.secondary);

        this.searchAid.addFilter(this.tr("Last modification"), "mod-time", {
            "all": { name: this.tr("All"), count: items.length },
            "hour": { name: this.tr("Last hour"), count: modifiedCounters.hour },
            "day": { name: this.tr("Last 24 hours"), count: modifiedCounters.day },
            "week": { name: this.tr("Last week"), count: modifiedCounters.week },
            "month": { name: this.tr("Last month"), count: modifiedCounters.month },
            "year": { name: this.tr("Last year"), count: modifiedCounters.year }
        }, this.__selection['mod-time']);
      }
    },

    __sortByRelevance: function(a, b){
      return (b.getRelevance() - a.getRelevance());
    },

    /**
     *  Highlights query strings in the given string
     */
    _highlight : function(string, query) {
        var reg = new RegExp('(' + qx.lang.String.escapeRegexpChars(query) + ')', "ig");
        return string.replace(reg, "<b>$1</b>");
    },

    /**
     * Act on backend events related to object modifications
     * and remove, update or add list item of the result list.
     *
     */
    _handleObjectEvent: function(e) {
      if (!this._old_query || this._old_query.trim() === "") {
        // nothing searched yet, skip the update
        return;
      }

      // Keep track of each event uuid we receive
      var data = e.getData();
      if(data.changeType == "remove"){
        this._removedObjects.push(data.uuid);
      }
      if(data.changeType == "create"){
        this._createdObjects.push(data.uuid);
      }
      if(data.changeType == "update" || data.changeType == "move") {
        this._modifiedObjects.push(data.uuid);
      }

      // Once an event was catched, start a new query, but do not show
      // the result in the list, instead just return it.
      if (this.__searchPromise) {
        this.__searchPromise.cancel();
      }
      this.__searchPromise = this.doSearch(true).then(function(result) {

          // Check for differences between the currently active result-set
          // and the fetched one.
          var added = [];
          var removed = [];
          var stillthere = [];
          var entries_by_uuid = {};

          // Create a list containing all currently show entry-uuids.
          var current_uuids = [];
          for(var i=0; i<this._currentResponse.results.length; i++){
            current_uuids.push(this._currentResponse.results[i].uuid);
            entries_by_uuid[this._currentResponse.results[i].uuid] = this._currentResponse.results[i];
          }

          // Create  list of all entry-uuids that ware returned by the query.
          var uuids = [];
          for(i=0; i<result.length; i++){
            uuids.push(result[i].uuid);
            entries_by_uuid[result[i].uuid] = result[i];
          }

          // Check which uuids were new, which were removed and which uuids are still there
          removed = qx.lang.Array.exclude(qx.lang.Array.clone(current_uuids), uuids);
          added = qx.lang.Array.exclude(qx.lang.Array.clone(uuids), current_uuids);
          stillthere = qx.lang.Array.exclude(current_uuids, added);
          stillthere = qx.lang.Array.exclude(stillthere, removed);

          // Walk through collected "remove-event" uuids and check if they were in our list
          // before, but are now gone. If so, then fade it out.
          // If its no longer in our list, but was not removed before (e.g just moved) then
          // just remove it from the list without fading it out.
          for(i=0; i<removed.length; i++){
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
          for(i=0; i<stillthere.length; i++){
            if(qx.lang.Array.contains(this._modifiedObjects, stillthere[i])){
              this.__updateEntry(entries_by_uuid[stillthere[i]]);
              this.updateFilter();
            }
            qx.lang.Array.remove(this._modifiedObjects, stillthere[i]);
          }

          // If there is a new entry in the result and we've got an create event
          // then fade the new entry in the result list.
          for(i=0; i<added.length; i++){
            if(qx.lang.Array.contains(this._createdObjects, added[i])){
              this.__fadeIn(entries_by_uuid[added[i]]);
            }else{
              this.__addEntry(entries_by_uuid[added[i]]);
            }
            this.updateFilter();
            qx.lang.Array.remove(this._createdObjects, added[i]);
          }
        }, this);
    },


    /**
     *  Update the given result-list item of the search-result-list
     * and reload the model.
     */
    __updateEntry: function(entry){

      // Locate the search result item in the search result model
      // and update it.
      var model = this.resultList.getModel();
      for(var i=0; i<model.getLength(); i++){
        if(entry.uuid == model.getItem(i).getUuid()){
          var item = model.getItem(i);
          item = this.__fillSearchListItem(item, entry);
          model.setItem(i, item);
          this.resultList.setModel(model);
          break;
        }
      }

      // Now remove the entry from the current result set
      for(i=0; i<this._currentResponse.results.length; i++){
        if(this._currentResponse.results[i].uuid == entry.uuid){
          this._currentResponse.results[i] = entry;
          break;
        }
      }
    },


    /**
     *  Adds a new entry to the search result-model
     */
    __addEntry: function(entry){

      // Add the given result-item to the list
      // and update the model
      var model = this.resultList.getModel();
      var item = new gosa.data.model.SearchResultItem();
      item = this.__fillSearchListItem(item, entry);
      model.push(item);
      this.resultList.setModel(model);

      // Also add this result-item to the current result set,
      // else we would add the item the the result-list
      // again and again and ...
      this._currentResponse.results.push(entry);
    },


    /**
     * Removes the given search-result entry from the result-list
     * and updates the model.
     */
    __removeEntry: function(entry){

      // Locate the model entry with the given uuid
      // and then remove it from the model.
      var model = this.resultList.getModel();
      for(var i=0; i<model.getLength(); i++){
        if(entry.uuid == model.getItem(i).getUuid()){
          qx.lang.Array.remove(model, model.getItem(i));
          this.resultList.setModel(model);
          break;
        }
      }

      // Now remove the entry from the current result set.
      for(i=0; i<this._currentResponse.results.length; i++){
        if(this._currentResponse.results[i].uuid == entry.uuid){
          qx.lang.Array.remove(this._currentResponse.results, this._currentResponse.results[i]);
          break;
        }
      }
    },


    /**
     *  Returns the model item for a given uuid
     */
    __getModelEntryForUUID: function(uuid){
      var model = this.resultList.getModel();
      for(var i=0; i<model.getLength();i++){
        if(model.getItem(i).getUuid() == uuid){
          return(model.getItem(i));
        }
      }
      return(null);
    },


    /**
     * Fades out the given search-result entry and finally
     * removes it.
     */
    __fadeOut: function(entry){
      this.__removeEntry(entry);
    },


    /**
     *  Adds the given search result entry to the list
     * and then starts a fade-in transition for it.
     */
    __fadeIn: function(entry){
      this.__addEntry(entry);
    },


    /**
     * Updates the properties of an 'gosa.data.model.SearchResultItem' using
     * the given search-result-entry.
     */
    __fillSearchListItem: function(item, entry){

      // Set the uuid first, this triggers a reset on the widget side.
      item.setUuid(entry.uuid);

      // Icon fallback to server provided images
      var icon = entry['icon'] ? entry['icon'] : gosa.util.Icons.getIconByType(entry['tag'], 64);

      item.setDn(entry.dn);
      item.setTitle(entry.title);
      item.setLastChanged(entry.lastChanged);
      item.setRelevance(entry.relevance);
      item.setSecondary(entry.secondary);
      item.setType(entry.tag);
      item.setDescription(this._highlight(entry.description, this._old_query));
      item.setIcon(icon);
      return(item);
    }
  },

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct : function() {
    if (this.__searchPromise) {
      this.__searchPromise.cancel();
      this.__searchPromise = null;
    }
    var sse = gosa.io.Sse.getInstance();
    sse.removeListener("objectModified", this.__debouncedReload, this);
    sse.removeListener("objectCreated", this.__debouncedReload, this);
    sse.removeListener("objectRemoved", this.__debouncedReload, this);
    sse.removeListener("objectMoved", this.__debouncedReload, this);
  }
});
