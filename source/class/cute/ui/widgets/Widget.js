qx.Class.define("cute.ui.widgets.Widget", {

  extend: qx.ui.container.Composite,

  construct: function(){
    this.base(arguments);  
  },

  properties : {
    multivalue : {
      check : 'Boolean',
      apply: '_applyMultivalue',
      init: false
    },

    value : {
      init : null,
      check : "qx.data.Array",
      nullable: true,
      event: 'changedValue',
      apply: '_applyValue'
    },

    required : {
      init : null,
      check : 'Boolean',
      nullable: false
    },

    placeholder : {
      init : null,
      nullable: true
    },

    maxLength : {
      init : null,
      nullable: true
    },

  },

  events: {
    "changedByTyping" : "qx.event.type.Event",
    "changedByFocus" : "qx.event.type.Event"
  },

  members: {

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
