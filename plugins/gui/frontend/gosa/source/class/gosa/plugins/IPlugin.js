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

/**
* Interface for all plugins that can be loaded via qx.io.PartLoader
*/
qx.Interface.define("gosa.plugins.IPlugin", {

  /*
  *****************************************************************************
     STATICS
  *****************************************************************************
  */
  statics : {
    /**
     * Unique name of the widget
     */
    NAME: ""
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {

    /**
     * Create the widget
     */
    draw: function() { },

    /**
     * Configure the widget
     * @param properties {Map} Key/value map of properties
     */
    configure: function(properties) {},

    /**
     * Returns the widgets configuration settings, which usually is the Map of user defined properties
     */
    getConfiguration: function() {}
  }
});