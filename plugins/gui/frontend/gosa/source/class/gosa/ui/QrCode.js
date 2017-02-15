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
 * Class implemeneting a wrapper to qrcode.js
 *
 * @ignore(QRCode)
 */
qx.Class.define("gosa.ui.QrCode", {
  extend : qx.ui.core.Widget,

  /*
   *****************************************************************************
   CONSTRUCTOR
   *****************************************************************************
   */

  /**
   * Construct a QR code widget.
   *
   * @param code {String} Code to visualize
   * @param size {Number} Size of the widget
   */
  construct : function(code, size)
  {
    this.base(arguments);

    if (code) {
      this.setCode(code);
    }

    if (size) {
     this.setSize(size);
    }
    else {
      this.initSize();
    }
  },

  /*
   *****************************************************************************
   PROPERTIES
   *****************************************************************************
   */

  properties :
  {
    /**
     * Current code to be visualized.
     */
    code : {
      check : "String",
      init : null,
      apply : "_applyCode",
      event : "changeCode"
    },

    /**
     * Size of the QR code.
     */
    size : {
      init : 100,
      themeable : true,
      check : "Integer",
      apply : "_applySize"
    }
  },

  /*
   *****************************************************************************
   MEMBERS
   *****************************************************************************
   */

  members :
  {
    // property apply
    _applySize : function(value)
    {
      this.setWidth(value);
      this.setHeight(value);

      if (this.getCode()) {
        this._generateWhenReady();
      }
    },

    // property apply
    _applyCode : function(value)
    {
      this._generateWhenReady();
    },

    /**
     * Calls {this._generate} when the DOM element is available
     * @private
     */
    _generateWhenReady : function()
    {
      if (this.getBounds()) {
        this.__generate();
      }
      else {
        this.addListenerOnce("appear", function() {
          this.__generate();
        }, this);
      }
    },

    /**
     * Delete old QRCodes in the DOMTree
     * and generate a new one
     * @private
     */
    __generate : function()
    {
      // Remove old QRCodes
      while (this.getContentElement().getDomElement().firstChild) {
        this.getContentElement().getDomElement().removeChild(this.getContentElement().getDomElement().firstChild);
      }

      if (this.getCode()) {
        var qrcode = new QRCode(this.getContentElement().getDomElement(), {
          width : this.getSize(),
          height : this.getSize()
        });

        qrcode.makeCode(this.getCode());
      }
    }
  }
});
