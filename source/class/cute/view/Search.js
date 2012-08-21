/* ************************************************************************

   Copyright: Cajus Pollmeier <pollmeier@gonicus.de>

   License:

   Authors:

************************************************************************ */

/* ************************************************************************

#asset(cute/*)

************************************************************************ */

qx.Class.define("cute.view.Search",
{
  extend : qx.ui.tabview.Page,

  construct : function()
  {
    var barWidth = 200;

    // Call super class and configure ourselfs
    this.base(arguments, "", cute.Config.getImagePath("apps/search.png", 32));
    this._excludeChildControl("label");
    this.setLayout(new qx.ui.layout.VBox(5));

    // Create search field / button
    var searchHeader = new qx.ui.container.Composite();
    var searchLayout = new qx.ui.layout.HBox(10);
    searchHeader.setLayout(searchLayout);

    var sf = new qx.ui.form.TextField();
    sf.setPlaceholder(this.tr("Please enter your search..."));
    this.addListener("resize", function() {
      sf.setWidth(parseInt(this.getBounds().width / 2));
    }, this)
    searchHeader.add(sf);

    var sb = new qx.ui.form.Button(this.tr("Search"));
    searchHeader.add(sb);
    searchHeader.setPadding(20);

    searchLayout.setAlignX("center");

    this.add(searchHeader);

    // Create search info (hidden)
    this.searchInfo = new qx.ui.container.Composite(new qx.ui.layout.HBox(10));
    this.searchInfo.hide()
    this.searchInfo.setPadding(20);
    this.searchInfo.setDecorator("separator-vertical");
    var sil = new qx.ui.basic.Label(this.tr("Search"));
    sil.setTextColor("red");
    //TODO: use custom theme font
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
    this.searchResult.hide()
    this.searchResult.setPadding(20);
    this.searchResult.setDecorator("separator-vertical");

    //TODO: fill the right bar with proper contents with proper contents

    var resultList = new qx.ui.form.List();
    resultList.setAppearance("SearchList");
    resultList.setDecorator(null);
    this.searchResult.add(resultList, {left: barWidth, right: 0, bottom: 0, top: 0});

    this.add(this.searchResult, {flex: 1});

    // Bind search methods
    // TODO: search while typing
    sb.addListener("execute", this.doSearch, this);
    sf.addListener("changeValue", this.doSearch, this);
    this.sf = sf;

    // Bind search result model
    var data = new qx.data.Array();
    this.resultController = new qx.data.controller.List(data, resultList, "dn");

    var that = this;
    this.resultController.setDelegate({
        createItem: function(){
          var item = new cute.ui.SearchListItem();
          item.addListener("edit", function(e){
              item.setIsLoading(true);
              that.openObject(e.getData().getDn());
              var lid = that.addListener("loadingComplete", function(e){
                  if(e.getData()['obj'].dn == item.getDn()){
                    item.setIsLoading(false);
                    that.removeListenerById(lid);
                  }
                }, that);
            }, this);

          item.addListener("remove", function(e){
              var dialog = new cute.ui.dialogs.RemoveItem(e.getData().getDn());
              dialog.addListener("remove", function(){
                  that.removeObject(item.getDn());
                }, this);
              dialog.open();
              
            }, this);
          return(item);
        },

        bindItem : function(controller, item, id) {
          controller.bindProperty("title", "title", null, item, id);
          controller.bindProperty("dn", "dn", null, item, id);
          controller.bindProperty("description", "description", null, item, id);
          controller.bindProperty("icon", "icon", null, item, id);
          controller.bindProperty("", "model", null, item, id);
        }
      });

    // Bind click
    //resultList.addListener("click", this.editItem, this);

    // Focus search field
    var _self = this;
    setTimeout(function() {
      _self.sf.focus();
    });
    this.sf.focus();
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
    doSearch : function() {
      var rpc = cute.io.Rpc.getInstance();
      rpc.cA(function(result, error){
        if(!error){
          var base = result;
          var startTime = new Date().getTime();
          rpc.cA(function(result, error){
              var endTime = new Date().getTime();
              this.showSearchResults(result, endTime - startTime);
          }, this, "search", "SELECT User.* BASE User SUB \"" + base + "\" WHERE User.uid like \"" + this.sf.getValue() + "\" ORDER BY User.sn");
        }
      }, this, "getBase");
    },

    showSearchResults : function(items, duration) {
      var i = items.length;

      if (i == 0){
        this.searchInfo.show()
        this.searchResult.hide()
      }

      var d = Math.round(duration / 100) / 10;
      this.sii.setValue(this.trn("%1 result", "%1 results", i, i) + " (" + this.trn("%1 second", "%1 seconds", d, d) + ")");

      this.searchInfo.show()
      this.searchResult.show()

      var model = [];

      // Dummy feeding for the moment...
      for (var i= 0; i<items.length; i++) {
        var item = new cute.data.model.SearchResultItem();
        item.setDn(items[i]['User'].DN[0]);
        item.setTitle(items[i]['User'].cn[0]);
        item.setType("User");
        item.setDescription("This is a multiline <i>description</i> featuring rich text<br>and some special <a href='clacks://cn=admin,dc=gonicus,dc=de'>links</a> to somewhere else.");
        //TODO: icon should be able to take path or base64 data
        item.setIcon(null);
        model.push(item);
      }
      
      // Update model
      this.resultController.setModel(new qx.data.Array(model));
    },

    editItem : function() {
      this.openObject(this.resultController.getSelection().getItem(0).getDn());
    },

    /* Removes the object given by dn and reloads the search results afterwards
     * #TODO: Add error handling for RPC errors.
     * */
    removeObject: function(dn){
      cute.proxy.ObjectFactory.openObject(function(obj, error){
          obj.remove(function(result, error){
              this.doSearch();
            }, this);
        }, this, dn); 
    },

    openObject : function(dn) {
      var w = null;
      var win = null;
      var _current_object = null;

      cute.proxy.ObjectFactory.openObject(function(obj, error){

        // Check for errors
        if(error){
          new cute.ui.dialogs.Error(error.message).open();
          return;
        }

        _current_object = obj;

        // Build widget and place it into a window
        cute.ui.Renderer.getWidget(function(w){
          win = new qx.ui.window.Window(this.tr("Object") + ": " + obj.dn);
          win.setLayout(new qx.ui.layout.VBox(10));
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
          var props = w.getProperties_();
          var doc = qx.core.Init.getApplication().getRoot();
          doc.add(win);

          this.fireDataEvent("loadingComplete", {obj: obj, widget: win});

        }, this, obj);
      }, this, dn);

    }
  }
});
