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
    this.setFocusable(true);

    this.addListener("appear", function(){
        this._visible = true;
      }, this);

    this.addState("cuteWidget");
  },

  properties : {
    
    valid: {
      check: "Boolean",
      event: "_validChanged",
      init: true
    },

    invalidMessage: {
      check: "String",
      event: "_invalidMessageChanged",
      init: ""
    },

    attribute: {
      check: "String",
      init: null
    },

    labelText: {
      check: "String",
      init: null
    },


    extension: {
      check: "String",
      init: null
    },

    guiProperties: {
      apply: "_applyGuiProperties",
      init: null
    },

    caseSensitive: {
      init: false
    },

    blockedBy: {
      init: false
    },

    defaultValue: {
      init: null,
      nullable: true
    },

    dependsOn: {
      init: null,
      nullable: true
    },

    mandatory: {
      init: false,
      apply: "_applyMandatory"
    },

    multivalue: {
      init: false
    },
    
    readonly: {
      init: false
    },

    type: {
      init: false
    },

    unique: {
      init: false
    },

    /* The values to display as selectables in the dropdown box
     * */ 
    values: {
      apply : "_applyValues",
      init : null 
    },

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
    }
  },

  events: {
    "changeValue" : "qx.event.type.Data"
  },

  members: {

    _was_initialized: false,
    _visible : false,
    name: null,

    /* Apply collected gui properties to this widet
     * */
    _applyGuiProperties: function(props){
      if(props["placeholderText"] && props["placeholderText"]["string"]){
        this.setPlaceholder(props["placeholderText"]["string"]);
      }
      if(props["echoMode"] && props["echoMode"]["enum"]){
        var echomode = props["echoMode"]["enum"];
        if (echomode == "QLineEdit::Password") {
          this.setEchoMode('password');
        } else if (echomode == "QLineEdit::NoEcho") {
          this.error("*** TextField NoEcho not supported!");
          return null;
        } else if (echomode == "QLineEdit::PasswordEchoOnEdit") {
          this.error("*** TextField NoEcho not supported!");
          return null;
        }
      }
      if(props["maxLength"] && props["maxLength"]["number"]){
        this.setMaxLength(parseInt(props["maxLength"]["number"])) ;
      }
    },

    shortcutExecute : function(){},

    _applyReadOnly: function(bool)
    {
      this.setEnabled(!bool);
    },

    _applyRequired: function(bool){
    },

    _applyValues: function(){},

    /* Apply method prototypes...
     * */
    focus:  function(){
    },

    resetInvalidMessage: function(){
      this.setValid(true);
      this.setInvalidMessage(true);
    },

    _applyValue: function(value){
    },

    _applyMultivalue: function(value){
    },

    _applyMandatory: function(value){
    }
  }
});
