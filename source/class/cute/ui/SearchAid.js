qx.Class.define("cute.ui.SearchAid",
{
  extend : qx.ui.core.Widget,

  construct : function() {
    // Call super class and configure ourselfs
    this.base(arguments);
    this.setLayout(new qx.ui.layout.VBox(10, "middle", "separator-vertical"));

    this.__filters = [];
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
	  addFilter : function(title, cat, elements){
	    var w = new qx.ui.groupbox.GroupBox(title);
      var group = new qx.ui.form.RadioGroup();

	    for (var k in elements) {
	      var v = elements[k];
	      var b = new qx.ui.form.ToggleButton(v);
	      w.add(b);
	      group.add(b);
	    }
	    
	    var that = this;
	    group.addListener("changeSelection", function() {
	      that.fireEvent("filterChanged", {
	          "category": cat,
	          "selection": this.getSelection()
	        });
	      }, group);
	    
	    this.__filters.push(w);
	    this.add(w);
	  },
	  
	  resetFilter : function() {
	    for (var i= 0; i<this.__filters.length; i++){
	      this.remove(this.__filters[i]);
	      dispose(this.__filters[i]);
	    }
	    
	    this.__filters = [];
	  }
	  
  }
});