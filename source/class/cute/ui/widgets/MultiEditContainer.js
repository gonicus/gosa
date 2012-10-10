/* This is the visible part of the multiedit widgets
 * or in more detail it is just one line of an multi-edit widget.
 * If you've set more than one telehpone number, for example, then 
 * each entry is represented by this widget.
 * 
 * It is just a container for the real-widget with additional buttons (add/del)
 * */
qx.Class.define("cute.ui.widgets.MultiEditContainer", {

  extend: qx.ui.container.Composite,

  properties: {

    // The widget to show
    widget: {
      init: null,
      apply: "__applyWidget"
    },

    // is the add-button visible?
    hasAdd: {
      check: "Boolean",
      init: false,
      apply: "__applyHasAdd"
    },

    // is the delete-button visible?
    hasDelete: {
      check: "Boolean",
      init: false,
      apply: "__applyHasDelete"
    }
  },

  construct: function(widget){
    this.base(arguments);

    this.setLayout(new qx.ui.layout.HBox(0));
  
    // Build up the buttons and a container which will later contain 
    // the real-widget and the buttons.
    this.__container = new qx.ui.container.Composite(new qx.ui.layout.HBox(0));
    this.__addButton = new qx.ui.form.Button(null, cute.Config.getImagePath("actions/attribute-add.png", "22")).set({
            "padding": 2,
            "margin": 0
            });
    this.__addButton.setAppearance("attribute-button");
    this.__addButton.setToolTip(new qx.ui.tooltip.ToolTip(this.tr("Add value")));
    this.__delButton = new qx.ui.form.Button(null, cute.Config.getImagePath("actions/attribute-remove.png", "22")).set({
            "padding": 2,
            "margin": 0
            });
    this.__delButton.setAppearance("attribute-button");
    this.__delButton.setToolTip(new qx.ui.tooltip.ToolTip(this.tr("Remove value")));

    // Add the created container to ourselves to make it visible.
    this.add(this.__container, {flex: 1});
    this.add(this.__addButton);
    this.add(this.__delButton);

    // Fire events once a button is clicked
    this.__addButton.addListener("execute", function(){
        this.fireEvent("add");
      }, this);

    this.__delButton.addListener("execute", function(){
        this.fireEvent("delete");
      }, this);

    if(widget){
      this.setWidget(widget);
    }
  },

  destruct : function(){
    this._disposeObjects("__container", "__addButton", "__delButton");
  },

  /* Events we can fire up
   * */
  events: {
    "add": "qx.event.type.Event",
    "delete": "qx.event.type.Event"
  },

  members: {
    __addButton: null,
    __delButton: null,
    __container: null,

    /* Applies the widget and puts it in the container to make it visible
     * */
    __applyWidget: function(w){
      this.__container.removeAll();
      if(w){
        this.__container.add(w, {flex:1});
      }
    },

    /* Applies the add button state and shows/hides it accordingly
     * */
    __applyHasAdd: function(value){
      if(value){
        this.__addButton.show();
      }else{
        this.__addButton.exclude();
      }
    },

    /* Applies the delete button state and shows/hides it accordingly
     * */
    __applyHasDelete: function(value){
      if(value){
        this.__delButton.show();
      }else{
        this.__delButton.exclude();
      }
    }
  }
});
