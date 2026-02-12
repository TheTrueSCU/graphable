# `graphable`

Graphable CLI (Rich)

**Usage**:

```console
$ graphable [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `info`: Get summary information about a graph.
* `check`: Validate graph integrity (cycles and...
* `reduce`: Perform transitive reduction on a graph...
* `convert`: Convert a graph between supported formats.

## `graphable info`

Get summary information about a graph.

**Usage**:

```console
$ graphable info [OPTIONS] FILE
```

**Arguments**:

* `FILE`: Input graph file  [required]

**Options**:

* `--help`: Show this message and exit.

## `graphable check`

Validate graph integrity (cycles and consistency).

**Usage**:

```console
$ graphable check [OPTIONS] FILE
```

**Arguments**:

* `FILE`: Input graph file  [required]

**Options**:

* `--help`: Show this message and exit.

## `graphable reduce`

Perform transitive reduction on a graph and save the result.

**Usage**:

```console
$ graphable reduce [OPTIONS] INPUT OUTPUT
```

**Arguments**:

* `INPUT`: Input graph file  [required]
* `OUTPUT`: Output graph file  [required]

**Options**:

* `--help`: Show this message and exit.

## `graphable convert`

Convert a graph between supported formats.

**Usage**:

```console
$ graphable convert [OPTIONS] INPUT OUTPUT
```

**Arguments**:

* `INPUT`: Input graph file  [required]
* `OUTPUT`: Output graph file  [required]

**Options**:

* `--help`: Show this message and exit.
