/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.io.types.Timestamp", 
{

  extend: qx.core.Object,

  construct: function(date){
    this.base(arguments); 
    this.set(date);
  },

  destruct : function(){
    this._date_obj = null;
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
      };

      if(this._date_obj){
        var content = 
          padStr(this._date_obj.getFullYear()) + "-" +
          padStr(this._date_obj.getMonth()+1) + "-" +
          padStr(this._date_obj.getDate()) + " " +
          padStr(this._date_obj.getHours()) + ":" +
          padStr(this._date_obj.getMinutes()) + ":" +
          padStr(this._date_obj.getSeconds());
        var data = {};
        data["__jsonclass__"] = gosa.io.types.Timestamp.tag;
        data["object"] = content;
        return(data);
      }else{
        return(null);
      }
    }
  }
});
