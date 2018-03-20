/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2018 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

/**
* Simple class with a key and a value property that can be used as model for lists.
*/
qx.Class.define('gosa.data.KeyValue', {
  extend: qx.core.Object,

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct: function (key, value, translateKey) {
    this.base(arguments);
    this._translateKey = translateKey === true;
    this.setKey(key);
    if (!value && translateKey === true) {
      this.setValue(qx.locale.Manager['tr'](key));
    } else {
      this.setValue(value);
    }
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties: {
    key: {
      check: 'String',
      init: null,
      event: 'changedKey'
    },
    value: {
      check: 'String',
      nullable: true,
      event: 'changedValue',
      transform: '_transformValue'
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members: {
    _translateKey: false,

    _transformValue: function (value) {
      if (this._translateKey === true && !value) {
        if (!this.getKey()) {
          // wait til key is set
          this.addListenerOnce('changedKey', function () {
            this.setValue(qx.locale.Manager['tr'](this.getKey()))
          }, this);
          return value;
        } else {
          return qx.locale.Manager['tr'](this.getKey())
        }
      }
      return value;
    }
  }
});