qx.Class.define("cute.data.SelectBoxItem",
{
  extend : qx.core.Object,

  properties : {
    name : {
      check : "String",
      event : "changeName"
    },

    icon : {
      check : "String",
      event : "changeIcon",
      nullable: true
    }
  },


  members : {
    toString: function() {
      return this.getName();
    }
  }

});
