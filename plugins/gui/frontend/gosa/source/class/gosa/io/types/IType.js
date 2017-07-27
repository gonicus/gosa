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

qx.Interface.define("gosa.io.types.IType", {
  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    get : function() {},
    set : function(value) {},
    toString : function() {},
    fromJSON : function(value) {},
    toJSON : function() {}
  }
});