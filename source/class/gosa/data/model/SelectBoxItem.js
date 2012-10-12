qx.Class.define("gosa.data.model.SelectBoxItem",
{
  extend : qx.core.Object,

  properties : {
    value : {
      check : "String",
      event : "changeValue"
    },

    key : {
      event : "changeKey",
      nullable: true
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
