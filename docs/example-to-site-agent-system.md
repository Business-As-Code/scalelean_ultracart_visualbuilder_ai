# Example-to-UltraCart agent system

Date: 2026-07-31.

## Product outcome

Given a reference website, screenshots, wireframe, or structured design brief,
an agent can rapidly build the corresponding UltraCart StoreFront experience
through Visual Builder. It selects legal elements, creates a valid hierarchy,
configures responsive behavior, preserves required dynamic commerce behavior,
applies bounded changes through the supported editor, and verifies the saved
and rendered result.

This is the new program target. Exhaustive manual widget discovery is not.

## What restarts and what remains

Restart:

- the one-browser-test-per-widget strategy;
- the assumption that the editor UI is the fastest catalog-discovery method;
- the old Home composition that treated Body as a layout parent;
- the 93 observed types as the complete product catalog.

Retain:

- the private source and artifact capture tools;
- the editor hierarchy and settings inspection methods;
- the save, reload, generated-VM, template, and public-render evidence model;
- the observed failure and session-recovery procedures;
- the privacy boundary and public-safe repository;
- the existing work as regression fixtures and historical evidence.

## Input contract

The system accepts one or more of:

- a public reference URL;
- desktop and responsive screenshots;
- a wireframe or annotated design;
- a written page specification;
- an approved asset and copy package;
- an existing UltraCart page to restyle or extend.

The intake result is a normalized design brief with:

- route type and commerce context;
- sections in order;
- layout and responsive intent;
- content and asset requirements;
- native dynamic behaviors that must be preserved;
- interactions and visibility rules;
- components that should be reusable imported containers;
- page-specific or context-managed regions;
- explicit unknowns and acceptance viewports.

## Agent skill architecture

### 1. Source registry query

Answers which elements exist, their settings, placement signals, forced-child
rules, context requirements, references, breakpoints, warnings, and known
anomalies. It reads the private normalized registry, not all 1,703 source files
for every task.

### 2. Reference analyzer

Converts the example into a semantic page specification. It separates visual
presentation from required storefront behavior. A static visual match must not
replace product price, inventory, cart, subscription, search, navigation, or
form behavior unless the brief explicitly permits that loss.

### 3. Hierarchy planner

Maps each semantic region to legal Visual Builder elements. It produces:

- template and imported-container composition;
- ordered widget trees;
- responsive layout choices;
- native data-bound branches to retain;
- candidate settings and asset references;
- source confidence and unresolved placement conflicts.

It keeps authoring-tree descendants separate from runtime-projected
descendants.

### 4. CJSON patch compiler

Compiles the plan into bounded operations such as insert, update, move,
replace-subtree, or remove. It validates the node contract, closed type set,
config keys, placement, references, inheritance, responsive values, and
ordering before any live action. It does not manufacture server-managed IDs or
runtime values.

### 5. Editor executor

Applies the smallest supported change through the Visual Builder editor. It
uses one writer, current session checks, parent-aware placement, targeted
widget changes, visible save confirmation, and checkpointed recovery. It does
not use undocumented APIs or FTP writes.

### 6. Persistence and render verifier

Tests the hierarchy after reload, persisted CJSON, generated Velocity,
template composition, public DOM, assets, geometry, interactions, and required
viewports. It reports each claim as Verified, Contradicted, or Unknown on its
specific evidence surface.

### 7. Learning and optimization loop

Promotes repeated successful procedures into recipes and regression tests. It
records elapsed time, browser actions, retries, failure class, and recovery
cost. It prefers source queries and deterministic checks over repeated visual
exploration.

## Build pipeline

~~~text
example
  -> normalized design brief
  -> semantic component plan
  -> legal Visual Builder hierarchy
  -> validated targeted patch plan
  -> approved editor execution
  -> save and reload verification
  -> persisted CJSON and generated VM verification
  -> public desktop and responsive acceptance
  -> reusable recipe and benchmark result
~~~

## Test strategy

Use a small benchmark suite instead of 563 isolated browser experiments:

1. Marketing Home page with shared header and footer, hero, grids, media,
   calls to action, forms, and responsive reflow.
2. Product page that preserves native item, pricing, subscription, inventory,
   purchase, and structured-data behavior.
3. Collection page with dynamic list, facets, sorting, pagination, and
   editorial content.
4. Content page with reusable imported sections and page-context behavior.
5. One overlay and complex-layout case covering Modal or Sidepanel, Tabs,
   Accordion, Slider, Table, Absolute, Masonry, and Flex structures.

Each benchmark has a reference, allowed differences, required native behavior,
viewports, and objective evidence checks.

## Efficiency measures

- time from accepted example to validated hierarchy plan;
- time from plan to saved first render;
- browser actions per inserted or changed widget;
- percentage of operations validated offline before browser use;
- save/reload failure and recovery rate;
- visual and structural acceptance pass rate;
- native commerce behavior retained;
- percentage of later builds satisfied by existing recipes.

The first benchmark establishes a baseline. Later skill changes must improve at
least one measure without reducing evidence quality or native behavior.

## Delivery sequence

1. Build and validate the private 563-element source registry.
2. Implement the source-query and hierarchy-validation libraries.
3. Define the normalized example and design-brief formats.
4. Implement the hierarchy planner and patch compiler with synthetic tests.
5. Repair the MELRA Home testbed and validate one minimal end-to-end patch.
6. Build the Home benchmark from an example.
7. Add product and collection benchmarks.
8. Package the reliable workflow as small composable Codex skills.
9. Run a fresh-agent acceptance test and publish only permitted, public-safe
   guidance and code.

## Acceptance

The program succeeds when a fresh Codex session can take an approved example,
produce a source-valid hierarchy and bounded patch plan, apply it through the
editor with one writer, and pass structural, persistence, generated-source,
render, responsive, and native-behavior checks. The benchmark must show a
measured improvement over the first manual build.
