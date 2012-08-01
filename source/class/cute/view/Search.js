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
    // Call super class and configure ourselfs
    this.base(arguments, "", "resource/cute/icons/search.png");
    this._excludeChildControl("label");
    this.setLayout(new qx.ui.layout.VBox(5));

    // Create search field / button
    var searchHeader = new qx.ui.container.Composite()
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

    // TODO: search while typing
    // Bind search methods
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
          rpc.cA(function(result, error){
              var list = new qx.data.Array();
              for(var i=0;i<result.length;i++){
                list.push(result[i]['User']);
              }
              console.log(list.toArray());

              if (list.length == 1) {
                this.openObject(list.getItem(0).DN[0]);
              } else {
                alert("Search was not unique...");
              }

          }, this, "search", "SELECT User.* BASE User SUB \"" + base + "\" WHERE User.uid = \"" + this.sf.getValue() + "\" ORDER BY User.sn");
        }
      }, this, "getBase");
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
