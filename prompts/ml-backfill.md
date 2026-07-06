# Mission: ML Training-Row Backfill

You reconstruct historical training rows so the ML sidecar can train before
enough live outcomes exist. For each target symbol, use its recorded backtest
events (get_backtest_summary shows them; the context pack shows the store).

Per historical event (symbol, report_date, and its known pre_close/post_open):

1. Fetch ~4 months of daily bars ENDING the day before the market reacted
   (for amc events: end_time = report_date end-of-day; for bmo: end the day
   BEFORE report_date). The bars must not include the reaction day — that
   would leak the label into the features.
2. `compute_indicators` on those bars. Embed the output verbatim under
   `"computed"` in the features JSON, plus `"event"`: {symbol, report_date,
   timing} and `"source": "reconstructed"`.
3. Label = the realized pre_close → post_open gap % (compute from the
   backtest row's stored prices; state your arithmetic).
4. `record_training_row(symbol, report_date, features_json, label_move_pct)`.

Rules:
- NEVER include reaction-day (or later) bars in the feature window — lookahead
  leakage poisons the model. If you can't cleanly bound the window for an
  event, skip it and say so.
- Real data only; skip events with missing/ambiguous prices.
- Work through every resolvable event for your targets, then report: rows
  recorded, rows skipped and why.
