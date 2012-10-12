qx.Class.define("gosa.ui.tabview.TabView",
{
  extend : qx.ui.tabview.TabView,


  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */


  /**
   * @param barPosition {String} Initial bar position ({@link #barPosition})
   */
  construct : function(barPosition)
  {
    this.base(arguments);
  },


  /*
  *****************************************************************************
     EVENTS
  *****************************************************************************
  */


  events :
  {
    /** Fires after the selection was modified */
    //"changeSelection" : "qx.event.type.Data"
  },


  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */


  properties :
  {
    // overridden
    menu :
    {
      check : qx.ui.form.MenuButton,
      nullable : true
    }
  },

  destruct : function(){
    this._disposeObjects("_tabContainer");
  },

  members :
  {

    // overridden
    _createChildControlImpl : function(id, hash)
    {
      var control = null;

      switch(id)
      {
        case "bar":
          control = new gosa.ui.container.SlideBar();
          control.setZIndex(10);
          this._add(control);
          break;

        case "pane":
          control = new qx.ui.container.Stack;
          control.setZIndex(5);
          this._add(control, {flex:1});
          break;
      }

      return control || this.base(arguments, id);
    }
  }
});
