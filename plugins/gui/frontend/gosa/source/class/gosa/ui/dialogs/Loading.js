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

qx.Class.define("gosa.ui.dialogs.Loading",
{
  extend : gosa.ui.dialogs.Dialog,

  construct : function()
  {
    this.base(arguments);
    this.getChildControl("captionbar").exclude();
    this.getChildControl("title").exclude();
    this.resetMinHeight();
    this.resetMinWidth();
    this._buttonPane.exclude();

    this._createChildControl("loading-label");

    this.addListenerOnce("resize", this.center, this);

    // subscribe to loading bus messages
    qx.event.message.Bus.subscribe('gosa.backend.state', this._onLoadingMessage, this);
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members: {
    __autoOpened: false,

    _onLoadingMessage: function(ev) {
      var control;
      var payload = ev.getData();
      if (payload.Type === "index") {
        if (!this.isActive()) {
          this.open();
          this.__autoOpened = true;
        }
        var progress = 100;
        this.getChildControl('loading-label').setLabel(this.tr("Indexing") + '...');
        if (payload.hasOwnProperty("Progress")) {
          progress = parseInt(payload.Progress, 10);
          control = this.getChildControl("progress");
          control.show();
          control.setValue(progress);
        } else {
          this.getChildControl("progress").exclude();
        }
        var lastStep = true;
        if (payload.hasOwnProperty("State")) {

          control = this.getChildControl("progress-info");
          control.show();
          var state = "";
          if (payload.hasOwnProperty("Step") && parseInt(payload.Step, 10)) {
            if (payload.hasOwnProperty("TotalSteps") && parseInt(payload.TotalSteps, 10)) {
              lastStep = (payload.TotalSteps - payload.Step) === 0;
              state = this.tr("Step %1 of %2", parseInt(payload.Step, 10), parseInt(payload.TotalSteps, 10));
            } else {
              state = this.tr("Step %1", parseInt(payload.Step, 10));
            }
            state += "<br/>" + payload.State;
          }
          control.setValue(state);
        }
        if (lastStep === true && progress === 100 && this.__autoOpened === true) {
          this.close();
          this.__autoOpened = false;
        }
      }
    },

    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {
        case 'loading-label':
          control = new qx.ui.basic.Atom(this.tr("Initializing") + "...", "@Ligature/time/22");
          control.setPadding([10, 20]);
          control.setAlignX("center");
          this.addAt(control, 0);
          break;

        case 'progress-info':
          control = new qx.ui.basic.Label();
          control.set({
            rich: true,
            wrap: true,
            textAlign: "center",
            allowGrowX: true
          });
          this.addAt(control, 1);
          break;

        case 'progress':
          control = new qx.ui.indicator.ProgressBar();
          control.setAlignX("center");
          control.exclude();
          this.addAt(control, 2);
          break;
      }

      return control || this.base(arguments, id);
    }
  },

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct: function () {
    qx.event.message.Bus.unsubscribe('gosa.loading', this._onLoadingMessage, this);
  }
});

