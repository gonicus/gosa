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
    this.base(arguments, "", "resource/cute/icons/search.png");
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

    searchLayout.setAlignX("left");

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
    resultList.setDecorator(null);
    this.searchResult.add(resultList, {left: barWidth, right: 0, bottom: 0, top: 0});

    this.add(this.searchResult, {flex: 1});

    // Bind search methods
    // TODO: search while typing
    sb.addListener("execute", this.doSearch, this);
    sf.addListener("changeValue", this.doSearch, this);
    this.sf = sf;
    var _self = this;

    // Focus search field
    setTimeout(function() {
      _self.sf.focus();
    });

    this.sf.focus();
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
          }, this, "search", "SELECT User.* BASE User SUB \"" + base + "\" WHERE User.uid = \"" + this.sf.getValue() + "\" ORDER BY User.sn");
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

      if (items.length) {
        // Populate result model
        //if (list.length == 1) {
        //  this.openObject(list.getItem(0).DN[0]);
        //} else {
        //  alert("Search was not unique...");
        //}
      }
    },


    openObject : function(dn) {
      var w = null;
      var win = null;
      var _current_object = null;

      cute.proxy.ObjectFactory.openObject(function(obj){
        _current_object = obj;

        // Build widget and place it into a window
        cute.ui.Renderer.getWidget(function(w){
          win = new qx.ui.window.Window(this.tr("Object") + ": " + obj.uuid);
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

        }, this, obj);
      }, this, dn);

    }
  }
});
