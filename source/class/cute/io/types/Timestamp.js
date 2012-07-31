qx.Class.define("cute.io.types.Timestamp", 
{

  extend: qx.core.Object,

  construct: function(date){
    this.base(arguments); 
    this.set(date);
  },

  statics: {
    tag: 'datetime.datetime'
  },

  members: {
    _date_obj : null,

    fromJSON: function(value){
      var m = value['object'].match(/(\d+)\-(\d+)\-(\d+) (\d+):(\d+):(\d+)/);

      // Create a native javascript Date instance (month is counted from 0!)
      this.set(new Date(m[1], m[2] -1, m[3], m[4], m[5], m[6]));
    },

    set: function(date){
      if(!date){
        date = null;
      }
      this._date_obj = date;  
    },

    get: function(){
      return(this._date_obj);
    },

    toJSON: function(){

      var padStr = function(i){
        return (i < 10) ? "0" + i : "" + i;
      }

      if(this._date_obj){
        var content = 
          padStr(this._date_obj.getFullYear()) + "-" +
          padStr(this._date_obj.getMonth()+1) + "-" +
          padStr(this._date_obj.getDate()) + " " +
          padStr(this._date_obj.getHours()) + ":" +
          padStr(this._date_obj.getMinutes()) + ":" +
          padStr(this._date_obj.getSeconds());
        return({__jsonclass__: cute.io.types.Timestamp.tag, object: content});
      }else{
        return(null);
      }
    }
  }
});
