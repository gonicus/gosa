qx.Class.define("cute.io.types.Binary", 
{

  extend: qx.core.Object,

  construct: function(data){
    this.base(arguments); 
    this.set(data);
  },

  statics: {
    tag: 'json.Binary'
  },

  members: {
    _data : null,

    fromJSON: function(value){
      this.set(value['object']);
    },

    set: function(data){
      if(!data){
        data = null;
      }
      this._data = data;  
    },

    get: function(){
      return(this._data);
    },

    toJSON: function(){
      if(this._data){
        return({__jsonclass__: cute.io.types.Binary.tag, object: this._data});
      }else{
        return(null);
      }
    }
  }
});
