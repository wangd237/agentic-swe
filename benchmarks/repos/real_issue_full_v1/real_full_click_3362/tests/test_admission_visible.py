import click


def test_usage_keeps_hyphenated_option_names_whole():
    args = "--precipitation-probability-by-hour --wind-speed-unit --cloud-cover"
    formatter = click.HelpFormatter(width=32)
    formatter.write_usage("report", args)
    rendered = formatter.getvalue()
    assert rendered.startswith("Usage: report")
    assert rendered[len("Usage: report"):].split() == args.split()
