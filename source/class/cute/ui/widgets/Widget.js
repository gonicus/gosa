/* This is the base class for all input-widgets created by 
 * the Renders class.
 *
 * It contains all necessary properties/methods and events to bind values,
 * set error messages, set placeholder...
 * */
qx.Class.define("cute.ui.widgets.Widget", {

  extend: qx.ui.container.Composite,

  construct: function(){
    this.name = this.classname.replace(/^.*\./, "");
    this.base(arguments);  
    this.setValue(new qx.data.Array());

    this.addListener("appear", function(){
        this._visible = true;
      }, this);
  },

  properties : {

    /* Whether the widget is a read only
     * */
    readOnly : {
      check : 'Boolean',
      apply: '_applyReadOnly',
      init: false
    },

    /* Whether the widget is a multi-value input or not.
     * */
    multivalue : {
      check : 'Boolean',
      apply: '_applyMultivalue',
      init: false
    },

    /* The value(s) for the widget.
     * All values (each when not multivalue) are of type qx.data.Array.
     * */
    value : {
      init : null,
      check : "qx.data.Array",
      nullable: true,
      event: 'changedValue',
      apply: '_applyValue'
    },

    /* Whether the field is required or not.
     * */
    required : {
      init : null,
      check : 'Boolean',
      nullable: false,
      apply: '_applyRequired'
    },

    /* The placeholder to use.
     * */
    placeholder : {
      init : null,
      nullable: true
    },

    /* The maximum length
     * */
    maxLength : {
      init : null,
      check : "Integer",
      nullable: true
    },

    /* Whether the widget was modified
     * */
    modified : {
      init : false,
      check : "Boolean"
    },

    definitions: {
      init: null,
      apply: "_applyPropertyDefinitions"
    }
  },

  events: {
    "changeValue" : "qx.event.type.Data"
  },

  members: {

    _was_initialized: false,
    _visible : false,
    name: null,

    _applyPropertyDefinitions: function(value){
      console.log(value);;
    },

    _applyReadOnly: function(bool)
    {
      this.setEnabled(!bool);
    },

    _applyRequired: function(bool){
    },

    /* Apply method prototypes...
     * */
    focus:  function(){
    },
    setValid: function(bool){
    },
    setInvalidMessage: function(message){
    },
    resetInvalidMessage: function(){
    },
    _applyValue: function(value){
    },
    _applyMultivalue: function(value){
    }
  }
});
