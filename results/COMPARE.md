# Content Understanding vs Document Intelligence: easy synthetic invoices

3 documents, three analyzers, scored against known values. A field expected to be absent counts correct only if the tool leaves it empty. 'Extra' lines are amounts a tool returned that are not on the document.

| Analyzer | Header fields correct | Line amounts found | Extra (invented) lines | Median seconds |
|---|---|---|---|---|
| Content Understanding custom analyzer `invoiceFields` | 30/30 (100%) | 10/10 (100%) | 0 | - |
| Content Understanding `prebuilt-invoice` | 30/30 (100%) | 10/10 (100%) | 0 | - |
| Document Intelligence `prebuilt-invoice` | 30/30 (100%) | 10/10 (100%) | 0 | - |

## Per file

| File | Analyzer | Header | Lines found | Extra | Seconds | Misses |
|---|---|---|---|---|---|---|
| invoice-01-clean.pdf | CU | 10/10 | 3/3 | 0 | - | - |
| invoice-01-clean.pdf | CUP | 10/10 | 3/3 | 0 | - | - |
| invoice-01-clean.pdf | DI | 10/10 | 3/3 | 0 | - | - |
| invoice-02-scanned.pdf | CU | 10/10 | 4/4 | 0 | - | - |
| invoice-02-scanned.pdf | CUP | 10/10 | 4/4 | 0 | - | - |
| invoice-02-scanned.pdf | DI | 10/10 | 4/4 | 0 | - | - |
| invoice-03-eu.pdf | CU | 10/10 | 3/3 | 0 | - | - |
| invoice-03-eu.pdf | CUP | 10/10 | 3/3 | 0 | - | - |
| invoice-03-eu.pdf | DI | 10/10 | 3/3 | 0 | - | - |

## Human review queue: fields with confidence < 0.8

| Analyzer | File | Field | Value | Confidence | Actually correct? |
|---|---|---|---|---|---|
| CUP | invoice-01-clean.pdf | PurchaseOrder | PO-55812 | 0.34 | yes |
| CUP | invoice-02-scanned.pdf | InvoiceTotal | 1764.1 | 0.41 | yes |
| CUP | invoice-03-eu.pdf | InvoiceTotal | 1722.52 | 0.41 | yes |
| DI | invoice-01-clean.pdf | InvoiceTotal | 1725.84 | 0.41 | yes |
| DI | invoice-01-clean.pdf | Currency | USD | 0.41 | yes |
| DI | invoice-02-scanned.pdf | InvoiceTotal | 1764.1 | 0.48 | yes |
| DI | invoice-02-scanned.pdf | Currency | USD | 0.48 | yes |
| DI | invoice-03-eu.pdf | InvoiceTotal | 1722.52 | 0.50 | yes |
| DI | invoice-03-eu.pdf | Currency | EUR | 0.50 | yes |
| CUP | invoice-03-eu.pdf | PurchaseOrder | LW-2209 | 0.53 | yes |
| CUP | invoice-01-clean.pdf | VendorName | Northwind Fabrication Co. | 0.56 | yes |
| CU | invoice-01-clean.pdf | Currency | USD | 0.60 | yes |
| CU | invoice-02-scanned.pdf | Currency | USD | 0.60 | yes |
| CUP | invoice-03-eu.pdf | VendorName | Tailspin Logistik GmbH | 0.60 | yes |
| CUP | invoice-02-scanned.pdf | PurchaseOrder | AW-7731 | 0.61 | yes |
| CUP | invoice-01-clean.pdf | CustomerName | Contoso Labs Ltd. | 0.61 | yes |
| CUP | invoice-02-scanned.pdf | CustomerName | Adventure Works Cycles | 0.61 | yes |
| CUP | invoice-03-eu.pdf | InvoiceId | TL/2026/00931 | 0.61 | yes |
| CUP | invoice-01-clean.pdf | DueDate | 2026-04-13 | 0.62 | yes |
| CUP | invoice-03-eu.pdf | DueDate | 2026-02-20 | 0.62 | yes |
| CUP | invoice-03-eu.pdf | CustomerName | Litware Retail SA | 0.64 | yes |
| CUP | invoice-01-clean.pdf | InvoiceId | NW-2026-0417 | 0.68 | yes |
| CUP | invoice-02-scanned.pdf | InvoiceId | FAB-88213 | 0.68 | yes |
| CUP | invoice-01-clean.pdf | InvoiceTotal | 1725.84 | 0.71 | yes |
| CUP | invoice-02-scanned.pdf | VendorName | Fabrikam Office Supply | 0.71 | yes |
| CUP | invoice-02-scanned.pdf | DueDate | 2026-03-04 | 0.72 | yes |
| CUP | invoice-03-eu.pdf | InvoiceDate | 2026-01-21 | 0.72 | yes |
| CUP | invoice-01-clean.pdf | InvoiceDate | 2026-03-14 | 0.78 | yes |
| CU | invoice-03-eu.pdf | Currency | EUR | 0.79 | yes |
| CUP | invoice-02-scanned.pdf | InvoiceDate | 2026-02-02 | 0.80 | yes |
