qx.Class.define("cute.data.model.SearchResultItem",
{
  extend : qx.core.Object,

  properties : {

    title : {
      check : "String",
      event : "changeTitle"
    },

    dn : {
      check : "String",
      event : "changeDn"
    },

    type : {
      check : "String",
      event : "changeType"
    },

    extensions : {
      check : "Array",
      event : "changeExtensions",
      nullable: true
    },

    description : {
      check : "String",
      event : "changeDescription",
      nullable: true
    },

    actions : {
      check : "Array",
      event : "changeActions",
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
      return this.getDn();
    }
  }

});
