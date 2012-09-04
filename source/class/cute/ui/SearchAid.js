qx.Class.define("cute.ui.SearchAid",
{
  extend : qx.ui.container.Composite,

  construct : function() {
    // Call super class and configure ourselfs
    this.base(arguments);
    this.setLayout(new qx.ui.layout.VBox(10, "top"));

    this.__filters = [];
    this.__selection = {};
  },

  events: {
    "filterChanged" : "qx.event.type.Data"
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */

  members :
  {
      getSelection : function() {
          return this.__selection;
      },

	  addFilter : function(title, cat, elements){
        var w = new qx.ui.groupbox.GroupBox(title);
        if (!title) {
            w.getChildControl("legend").exclude();
            w.getChildControl("frame").setMarginTop(0);
            w.getChildControl("frame").setPaddingTop(0);
        }
        w.setAppearance("SearchAid");
        w.setLayout(new qx.ui.layout.VBox(0));
        var group = new qx.ui.form.RadioGroup();

	    for (var k in elements) {
	      var v = elements[k];
	      var b = new qx.ui.form.ToggleButton(v);

          if (!this.__selection[cat]) {
              this.__selection[cat] = k;
          }

          b.setAppearance("SearchAidButton");
          b.setUserData("category", k);
	      w.add(b);
	      group.add(b);
	    }
	    
	    var that = this;
	    group.addListener("changeSelection", function() {
          var selection = this.getSelection()[0].getUserData("category")
          that.__selection[cat] = selection;
	      that.fireDataEvent("filterChanged", {
	          "category": cat,
	          "selection": selection
	        });
	      }, group);
	    
	    this.__filters.push(w);
	    this.add(w);
	  },

	  hasFilter : function() {
            return this.__filters.length != 0;
	  },
	  
	  resetFilter : function() {
	    for (var i= 0; i<this.__filters.length; i++){
	      this.remove(this.__filters[i]);
	    }
	    
	    this.__filters = [];
	    this.__selection = {};
	  }
	  
  }
});
