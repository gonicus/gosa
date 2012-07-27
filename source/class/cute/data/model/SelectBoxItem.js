qx.Class.define("cute.data.model.SelectBoxItem",
{
  extend : qx.core.Object,

  properties : {
    value : {
      check : "String",
      event : "changeValue"
    },

    key : {
      event : "changeKey"
    },

    icon : {
      check : "String",
      event : "changeIcon",
      nullable: true
    }
  },


  members : {
    toString: function() {
      return this.getValue();
    }
  }

});
