/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2016 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
* A singleton wrapper for {qx.ui.window.Desktop} to allow app-wide accessibility
*/
qx.Class.define("gosa.ui.window.Desktop", {
  extend : qx.ui.window.Desktop,
  type: "singleton"
});