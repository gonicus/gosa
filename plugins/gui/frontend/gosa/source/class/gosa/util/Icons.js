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
      'domain': '@Ligature/link',
      'sambamachineaccount': '@Ligature/windows',
      'groupofnames': '@Ligature/circle',
      'gotoprinter': '@Ligature/print',
      'gosaapplication': '@Ligature/app',
      'incomingdevicecontainer': '@Ligature/building',
      'organizationalrole': '@Ligature/building'
    },

    iconActionMappings: {
      'c': '@Ligature/add',
      'r': '@Ligature/view',
      'w': '@Ligature/write',
      'd': '@Ligature/trash'
    },

    getIconByAction: function(action) {
      return gosa.util.Icons.iconActionMappings[action];
    },

    getIconByType: function(type, size) {
      if (gosa.util.Icons.iconMappings[type.toLowerCase()]) {
        return gosa.util.Icons.iconMappings[type.toLowerCase()]
      } else {
        return null;
        var path = gosa.Config.spath + "/" + gosa.Config.getTheme() + "/resources/images/objects/"+size+"/" + type.toLowerCase() + ".png";
        path = document.URL.replace(/\/[^\/]*[a-zA-Z]\/.*/, "") + path;
        return path;
      }
    },

    /**
     * This converter can be used in icon bindings for tree items. e.g.
     *
     * <pre>
     *  controller.bindProperty("type", "icon", { converter: gosa.util.Icons.treeIconConverter }, item, index);
     * <pre>
     */
    treeIconConverter: function(data, model, source, target) {
      if (model.isDummy()) {
        return null;
      }
      if (!model.isLoading()) {
        if (target.$$animationHandle) {
          gosa.ui.Throbber.stopAnimation(target.getChildControl('icon'), target.$$animationHandle, true);
          delete target.$$animationHandle;
        }
        if (model.getType()) {
          return gosa.util.Icons.getIconByType(model.getType(), 22);
        }
        return "@Ligature/pencil";
      } else {
        if (target.getChildControl('icon').getBounds()) {
          target.$$animationHandle = gosa.ui.Throbber.animate(target.getChildControl('icon'));
        } else {
          target.getChildControl('icon').addListenerOnce('appear', function() {
            target.$$animationHandle = gosa.ui.Throbber.animate(target.getChildControl('icon'));
          }, this);
        }
        return "@Ligature/adjust";
      }
    },

    /**
     * Parse an icon received from the backend
     * @param data {String|Object} icon data can be a simple icon source string or stringified JSON data
     * @param property {String?} optional property to return (data must be an object or JSON string)
     * @returns {String} icon source path or property value
     */
    parse: function(data, property) {
      if (qx.lang.Type.isString(data) && data.startsWith("{")) {
        data = qx.lang.Json.parse(data.replace(/'/g, '"'));
      }
      if (property && qx.lang.Type.isObject(data) && data.hasOwnProperty(property)) {
        return data[property];
      }
      return data;

    }
  }
});
