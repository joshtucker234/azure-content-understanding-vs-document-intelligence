# Content Understanding vs Document Intelligence: harder documents (synthetic hard + real)

5 documents, three analyzers, scored against known values. A field expected to be absent counts correct only if the tool leaves it empty. 'Extra' lines are amounts a tool returned that are not on the document.

| Analyzer | Header fields correct | Line amounts found | Extra (invented) lines | Median seconds |
|---|---|---|---|---|
| Content Understanding custom analyzer `invoiceFields` | 49/50 (98%) | 42/43 (98%) | 1 | 13.0 |
| Content Understanding `prebuilt-invoice` | 49/50 (98%) | 42/43 (98%) | 1 | 30.9 |
| Document Intelligence `prebuilt-invoice` | 47/50 (94%) | 43/43 (100%) | 0 | 8.5 |

## Per file

| File | Analyzer | Header | Lines found | Extra | Seconds | Misses |
|---|---|---|---|---|---|---|
| hard-01-multipage.pdf | CU | 10/10 | 26/26 | 0 | 21.08 | - |
| hard-01-multipage.pdf | CUP | 10/10 | 26/26 | 0 | 71.03 | - |
| hard-01-multipage.pdf | DI | 10/10 | 26/26 | 0 | 7.64 | - |
| hard-02-fax.pdf | CU | 9/10 | 4/5 | 1 | 12.63 | InvoiceId: got 'NI-60417', want 'INI-60417' |
| hard-02-fax.pdf | CUP | 9/10 | 4/5 | 1 | 30.88 | InvoiceId: got 'NI-60417', want 'INI-60417' |
| hard-02-fax.pdf | DI | 9/10 | 5/5 | 0 | 8.5 | SubTotal: got 12413.4, want 1413.4 |
| hard-03-tricky.pdf | CU | 10/10 | 4/4 | 0 | 12.56 | - |
| hard-03-tricky.pdf | CUP | 10/10 | 4/4 | 0 | 30.27 | - |
| hard-03-tricky.pdf | DI | 10/10 | 4/4 | 0 | 7.85 | - |
| hf-invoice.pdf | CU | 10/10 | 7/7 | 0 | 12.97 | - |
| hf-invoice.pdf | CUP | 10/10 | 7/7 | 0 | 36.96 | - |
| hf-invoice.pdf | DI | 10/10 | 7/7 | 0 | 13.43 | - |
| hf-invoice_with_scribbles.pdf | CU | 10/10 | 1/1 | 0 | 13.65 | - |
| hf-invoice_with_scribbles.pdf | CUP | 10/10 | 1/1 | 0 | 21.45 | - |
| hf-invoice_with_scribbles.pdf | DI | 8/10 | 1/1 | 0 | 12.44 | CustomerName: got 'Future Solutions\nATTN: [contact name]', want 'Future Solutions'; InvoiceId: got 'nº2', want '2' |

## Human review queue: fields with confidence < 0.8

| Analyzer | File | Field | Value | Confidence | Actually correct? |
|---|---|---|---|---|---|
| CUP | hf-invoice.pdf | InvoiceTotal | 544.46 | 0.22 | yes |
| DI | hf-invoice_with_scribbles.pdf | VendorName | SIMEDIC | 0.34 | yes |
| CU | hf-invoice.pdf | Currency | USD | 0.35 | yes |
| CU | hf-invoice.pdf | SubTotal | 494.96 | 0.37 | yes |
| CUP | hard-03-tricky.pdf | InvoiceTotal | 4623.69 | 0.39 | yes |
| CUP | hard-02-fax.pdf | InvoiceTotal | 1512.34 | 0.41 | yes |
| CUP | hard-02-fax.pdf | PurchaseOrder | HL-30911 | 0.41 | yes |
| CUP | hard-02-fax.pdf | InvoiceId | NI-60417 | 0.42 | NO |
| DI | hard-02-fax.pdf | InvoiceTotal | 1512.34 | 0.42 | yes |
| DI | hard-02-fax.pdf | Currency | USD | 0.42 | yes |
| CUP | hard-02-fax.pdf | VendorName | Initech Parts & Service | 0.51 | yes |
| CUP | hard-03-tricky.pdf | PurchaseOrder | WW-PO-48820 | 0.51 | yes |
| CUP | hard-02-fax.pdf | DueDate | 2026-06-05 | 0.52 | yes |
| CUP | hf-invoice.pdf | VendorName | Williams LLC | 0.53 | yes |
| CUP | hf-invoice.pdf | CustomerName | Hernandez-Anderson | 0.55 | yes |
| DI | hard-03-tricky.pdf | PurchaseOrder | WW-PO-48820 | 0.57 | yes |
| DI | hard-03-tricky.pdf | VendorName | Wide World Importers Pty Ltd | 0.58 | yes |
| CU | hard-01-multipage.pdf | Currency | USD | 0.60 | yes |
| CU | hard-02-fax.pdf | Currency | USD | 0.60 | yes |
| CUP | hard-03-tricky.pdf | VendorName | Wide World Importers Pty Ltd | 0.61 | yes |
| CUP | hf-invoice_with_scribbles.pdf | DueDate | 2014-01-09 | 0.61 | yes |
| CUP | hard-02-fax.pdf | CustomerName | Hooli Logistics Inc. | 0.62 | yes |
| CU | hf-invoice_with_scribbles.pdf | InvoiceId | 2 | 0.62 | yes |
| CUP | hard-01-multipage.pdf | VendorName | Globex Industrial Supply | 0.63 | yes |
| CUP | hard-01-multipage.pdf | PurchaseOrder | 4500-88217 | 0.64 | yes |
| CUP | hf-invoice_with_scribbles.pdf | CustomerName | Future Solutions | 0.64 | yes |
| CUP | hard-03-tricky.pdf | DueDate | 2026-06-18 | 0.65 | yes |
| CUP | hard-01-multipage.pdf | DueDate | 2026-05-24 | 0.67 | yes |
| CUP | hard-02-fax.pdf | InvoiceDate | 2026-05-06 | 0.67 | yes |
| CUP | hard-03-tricky.pdf | InvoiceId | WWI-2026-3318 | 0.67 | yes |
| CUP | hf-invoice_with_scribbles.pdf | VendorName | SIMEDIC | 0.69 | yes |
| CUP | hard-01-multipage.pdf | InvoiceId | GL-771204 | 0.70 | yes |
| CUP | hard-01-multipage.pdf | CustomerName | Initrode Fabrication LLC | 0.71 | yes |
| CUP | hard-03-tricky.pdf | CustomerName | Blackwood Builders Co-operative | 0.72 | yes |
| CU | hf-invoice.pdf | TotalTax | 49.5 | 0.72 | yes |
| CUP | hf-invoice.pdf | InvoiceDate | 2012-10-09 | 0.72 | yes |
| CU | hard-02-fax.pdf | InvoiceId | NI-60417 | 0.73 | NO |
| CU | hard-02-fax.pdf | TotalTax | 98.94 | 0.73 | yes |
| DI | hf-invoice_with_scribbles.pdf | CustomerName | Future Solutions / ATTN: [contact name] | 0.73 | NO |
| CUP | hf-invoice_with_scribbles.pdf | InvoiceTotal | 1350 | 0.73 | yes |
| CU | hf-invoice.pdf | InvoiceTotal | 544.46 | 0.74 | yes |
| CUP | hf-invoice.pdf | InvoiceId | 27301261 | 0.75 | yes |
| DI | hf-invoice.pdf | SubTotal | 494.96 | 0.75 | yes |
| CUP | hard-01-multipage.pdf | InvoiceTotal | 21566.83 | 0.76 | yes |
| CU | hard-02-fax.pdf | InvoiceTotal | 1512.34 | 0.77 | yes |
| CU | hard-02-fax.pdf | SubTotal | 1413.4 | 0.78 | yes |
| CUP | hard-03-tricky.pdf | InvoiceDate | 2026-05-19 | 0.78 | yes |
| CUP | hf-invoice_with_scribbles.pdf | InvoiceId | 2 | 0.78 | yes |
| CUP | hard-01-multipage.pdf | InvoiceDate | 2026-04-09 | 0.78 | yes |
| CUP | hf-invoice_with_scribbles.pdf | InvoiceDate | 2014-01-09 | 0.79 | yes |
| DI | hard-02-fax.pdf | TotalTax | 98.94 | 0.79 | yes |
| CU | hard-02-fax.pdf | PurchaseOrder | HL-30911 | 0.79 | yes |
| DI | hf-invoice.pdf | TotalTax | 49.5 | 0.79 | yes |
