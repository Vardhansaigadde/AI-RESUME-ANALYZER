"""Service layer package.

Contains business logic, document extraction routines (PDF via pdfplumber,
DOCX via python-docx), ML inference pipelines, and recommendation generators.

Import from the submodules directly (e.g. ``app.services.pipeline``). The
package deliberately does not re-export them: eager imports here created a
circular import between app.services.pipeline and app.ml.features.
"""
