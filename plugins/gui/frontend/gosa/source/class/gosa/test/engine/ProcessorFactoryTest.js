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

qx.Class.define("gosa.test.engine.ProcessorFactoryTest",
{
  extend : qx.dev.unit.TestCase,

  members :
  {
    testProcessorFactory : function() {
      var factory = gosa.engine.ProcessorFactory;

      var json = JSON.parse('{"type" : "widget"}');
      this.assertInstance(factory.getProcessor(json), gosa.engine.processors.WidgetProcessor);

      json = JSON.parse('{"type" : "form"}');
      this.assertInstance(factory.getProcessor(json), gosa.engine.processors.FormProcessor);

      json = JSON.parse('{"type" : "foo"}');
      this.assertNull(factory.getProcessor(json));
    }
  }
});
