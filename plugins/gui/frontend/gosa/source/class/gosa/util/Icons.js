/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.util.Icons", {

  type: "static",

  statics: {

    iconMappings: {
      'organizationalunit': '@Ligature/building',
      'root': '@Ligature/sitemap',
      'organization': '@Ligature/building',
      'domaincomponent': '@Ligature/globe',
      'country': '@Ligature/globe',
      'user': '@Ligature/user',
      'aclrole': '@Ligature/key',
      'posixgroup': '@Ligature/group',
      'sambadomain': '@Ligature/server',
      'device': '@Ligature/pc',
      'locality': '@Ligature/location',
      'domain': '@Ligature/link'
      'sambamachineaccount': '@Ligature/windows'

    },

    iconActionMappings: {
      'c': '@Ligature/add',
      'r': '@Ligature/view',
      'w': '@Ligature/write',
      'd': '@Ligature/delete'
    },

    getIconByAction: function(action) {
      return gosa.util.Icons.iconActionMappings[action];
    },

    getIconByType: function(type, size) {
      if (gosa.util.Icons.iconMappings[type.toLowerCase()]) {
        return gosa.util.Icons.iconMappings[type.toLowerCase()]
      } else {
        var path = gosa.Config.spath + "/" + gosa.Config.getTheme() + "/resources/images/objects/"+size+"/" + type.toLowerCase() + ".png";
        path = document.URL.replace(/\/[^\/]*[a-zA-Z]\/.*/, "") + path;
        return path;
      }
    }
  }
});
