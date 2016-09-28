/*========================================================================

 This file is part of the GOsa project -  http://gosa-project.org

 Copyright:
 (C) 2010-2016 GONICUS GmbH, Germany, http://www.gonicus.de

 License:
 LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

 See the LICENSE file in the project's top-level directory for details.

 ======================================================================== */

qx.Class.define("gosa.util.Icons", {

  type: "static",

  statics: {

    iconMappings: {
      'organizationalunit': '@FontAwesome/f114', // folder-o
      'root': '@FontAwesome/sitemap',
      'organization': '@FontAwesome/f275', //'industry',
      'domaincomponent': '@FontAwesome/globe',
      'user': '@FontAwesome/user',
      'posixgroup': '@FontAwesome/f0c0', // users
      'sambadomain': '@FontAwesome/server'
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