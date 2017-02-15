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
 * Plugins represent widgets that can be externally loaded and added to the dashboard.
 * Those widgets can be included as every other class, loaded as external library as part or
 * as a completely self contained zip archive.
 */
/* EXAMPLE Dashboard setting
[
  {
    "widget" : "gosa.plugins.activity",
    "source" : "external",
    "layoutProperties" : {
      "rowSpan" : 5,
      "row" : 2,
      "colSpan" : 2,
      "column" : 0
    },
    "settings" : {}
  },
  {
    "widget" : "gosa.plugins.search",
    "source" : "builtin",
    "layoutProperties" : {
      "rowSpan" : 1,
      "row" : 1,
      "colSpan" : 6,
      "column" : 0
    },
    "settings" : {"minColSpan" : 3}
  },
  {
    "widget" : "gosa.plugins.yql",
    "source" : "external",
    "layoutProperties" : {
      "rowSpan" : 5,
      "row" : 2,
      "colSpan" : 2,
      "column" : 4
    },
    "settings" : {
      "title": "Heise News:",
      "query" : " select title, description, link from feed where url='https://www.heise.de/newsticker/heise.rdf' limit 25",
      "mapping" : {
        "description" : "description",
        "link" : "link",
        "title" : "title"
      }
    }
  },
  {
    "widget" : "gosa.plugins.yql",
    "source" : "external",
    "layoutProperties" : {
      "rowSpan" : 5,
      "row" : 2,
      "colSpan" : 2,
      "column" : 2
    },
    "settings" : {
      "title": "Git commit log:",
      "refreshRate" : 60,
      "query" : "select title, link.href, author.name, thumbnail.url from atom where url='https://github.com/gonicus/gosa/commits/master.atom' limit 10",
      "mapping" : {
        "title" : "title",
        "description" : "author.name",
        "link" : "link.href",
        "icon" : "thumbnail.url"
      }
    }
  },
  {
    "widget" : "gosa.plugins.workflowstarter",
    "source" : "builtin",
    "layoutProperties" : {
      "rowSpan" : 2,
      "row" : 7,
      "colSpan" : 2,
      "column" : 0
    },
    "settings" : {
      "maxColSpan" : 2,
      "workflow" : "create_user"
    }
  }
]*/
