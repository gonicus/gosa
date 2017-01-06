/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Search result model
 */
qx.Class.define("gosa.plugins.activity.model.SearchResult", {
  extend : qx.core.Object,
  include: qx.ui.form.MModelProperty,

  /*
   *****************************************************************************
   CONSTRUCTOR
   *****************************************************************************
   */
  construct : function() {
    this.base(arguments);

    this.setModel(new qx.data.Array());

    this.__marshaller = new qx.data.marshal.Json({
      getModelClass: function() {
        return gosa.data.model.SearchResultItem;
      },
      getPropertyMapping: function(property) {
        return property === "tag" ? "type" : property
      }
    })
  },

  /*
   *****************************************************************************
   PROPERTIES
   *****************************************************************************
   */
  properties : {
    highlight: {
      check: "String",
      nullable: true,
      event: "changeHighlight"
    }
  },

  /*
   *****************************************************************************
   MEMBERS
   *****************************************************************************
   */
  members : {
    __marshaller: null,

    updateModel: function(result) {
      this.__marshaller.toClass(result);
      this.setModel(this.__marshaller.toModel(result));
    }
  }
});