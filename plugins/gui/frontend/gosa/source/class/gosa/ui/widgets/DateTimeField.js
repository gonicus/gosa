/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.ui.widgets.DateTimeField", {

  extend: qx.ui.form.DateField,

  construct: function(){

    this.base(arguments);
    var format = new qx.util.format.DateFormat(
      qx.locale.Date.getDateFormat("short") + " " + qx.locale.Date.getTimeFormat("short"));

    this.setWidth(130);
    this.setDateFormat(format);
  },

  members: {

   /**
    * Handler method which handles the click on the calender popup.
    *
    * @param e {qx.event.type.Mouse} The mouse event of the click.
    */
    _onChangeDate : function(e)
    {
      var textField = this.getChildControl("textfield");
      var selectedDate = this.getChildControl("list").getValue();

      // Keep the selected HH:mm:ss part of the TextField and only 
      // use the YY:MM:dd part of the selection dialog. 
      var curDate = this.getValue();
      var format1 = new qx.util.format.DateFormat(qx.locale.Date.getDateFormat("short"));
      var format2 = new qx.util.format.DateFormat(qx.locale.Date.getTimeFormat("short"));
      
      var newStr = "";
      if(format1.format(selectedDate)){
        newStr = format1.format(selectedDate);

        if(format2.format(curDate)){
          newStr += " " + format2.format(curDate);
        }else{
          newStr = this.getDateFormat().format(selectedDate);
        }
      }
      textField.setValue(newStr);
      this.close();
    }
  }
});
