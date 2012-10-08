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
    this.searchAid.addListener("filterChanged", this.doSearchE, this);

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

    // Listen for object changes comming from the backend
    cute.io.WebSocket.getInstance().addListener("objectModified", function(e){
        var data = e.getData();
        if(this._lastUpdateReload != data['lastChanged']){
          var model = this.resultList.getModel().toArray();
          for(var i=0; i<model.length; i++){
            if(model[i].getUuid() == data['uuid']){
              this._lastUpdateReload = data['lastChanged'];
              this.doSearchE();
            }
          }
        }
        console.log("++ handeled event --- create --- in search result!")
      }, this);

    cute.io.WebSocket.getInstance().addListener("objectCreated", function(e){
        console.log("++ UNhandeled event --- create --- in search result!")
      }, this);

    cute.io.WebSocket.getInstance().addListener("objectRemoved", function(e){
        console.log("++ UNhandeled event --- remove --- in search result!")
      }, this);

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

    _search_queue_handler : function() {
      if (this._sq.length == 0 || this._working) {
        return;
      }

      // Lock us
      this._working = true;

      // Do search and lock ourselves
      this.doSearch(null, function() {
        this._working = false;
      }, false);
    },

    _handle_key_event : function(e) {
      // Push the search to the search queue
      if (this.sf.getValue().length > 2) {
        this._sq.push(this.sf.getValue());
      }
    },

    doSearchE : function(e, callback) {
      this._sq.push(this.sf.getValue());
      this.doSearch(e, callback, false);
    },

    doSearch : function(e, callback, reset) {
      var selection = this.searchAid.getSelection();
      var rpc = cute.io.Rpc.getInstance();

      // Remove all entries from the queue and keep the newest
      var query = "";
      while (true) {
         var q = this._sq.shift();
         if (!q) {
           break;
         }
         query = q;
      }
     
  
      // Don't search for nothing
      if (query == "") {
        if (callback) {
          callback.apply(this);
        }
        return;
      }
      
      // Memorize old query
      this._old_query = query;

      // Reset selection if required
      if (reset) {
          selection = this.__default_selection;
      }

      rpc.cA(function(result, error){
        if(!error){
          var base = result;
          var startTime = new Date().getTime();

          // Try ordinary search
          rpc.cA(function(result, error){
            var endTime = new Date().getTime();
            this.showSearchResults(result, endTime - startTime, false, query, reset);

            if (callback) {
              callback.apply(this);
            }
          }, this, "search", base, "sub", query, selection);
        }
      }, this, "getBase");
    },

    showSearchResults : function(items, duration, fuzzy, query, reset) {
      var i = items.length;

      this.searchInfo.show();
      this.resultList.getChildControl("scrollbar-x").setPosition(0);
      this.resultList.getChildControl("scrollbar-y").setPosition(0);

      if (i == 0 && reset){
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
      data.sort(function (a, b) {
          if (a.getRelevance() == b.getRelevance()) {
              return 0;
          }
          if (a.getRelevance() < b.getRelevance()) {
              return -1;
          }
          return 1;
      });
      
      this.resultList.setModel(data);
      
      // Add search filters
      var selection = this.searchAid.getSelection();
      if (reset || !categories[selection['category']]) {
        this.searchAid.resetFilter();
      } else {
        this.searchAid.resetFilter("category");
      }
      if (!this.searchAid.hasFilter()) {
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

        //TODO: list locations
      }
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
          win = new qx.ui.window.Window(this.tr("Object") + ": " + obj.dn);
          win.setLayout(new qx.ui.layout.VBox(10));
          win.setWidth(700);
          win.add(w);
          win.addListener("appear", win.center, win);
          win.open();

          // See http://bugzilla.qooxdoo.org/show_bug.cgi?id=1770
          win.setShowMinimize(false);

          w.addListener("done", function(){
            w.destroy();
            win.destroy();
          }, this);

          win.addListener("close", function(){
            obj.close();
            w.destroy();
            win.destroy();
          }, this);

          // Position window as requested
          var doc = qx.core.Init.getApplication().getRoot();
          doc.add(win);

          this.fireDataEvent("loadingComplete", {dn: dn});

        }, this, obj);
      }, this, dn);
    }
  }
});
