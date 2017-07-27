/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

qx.Class.define("gosa.io.types.Binary", 
{
  extend: qx.core.Object,
  implement: gosa.io.types.IType,

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

    toString: function() {
      return this.get();
    },

    toJSON: function(){
      if(this._data){
        var data = {};
        data["__jsonclass__"] = gosa.io.types.Binary.tag;
        data["object"] = this._data;
        return(data);
      }else{
        return(null);
      }
    }
  }
});
