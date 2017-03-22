PID Cat (extended)
==================

An update to Jake Wharton's excellent [pidcat][1] which filters `adb` result by application package name.

    pidcat com.oprah.bees.android

On top of this, this fork will mainly provide these additional options
 * `--timestamp`: add timestamp at the front of each line
 * `--grep`, `--highlight`, `--grepv`: grep, highlight or exclude lines. These options particularly consider the line cutting issue in `pidcat`. This script will grep lines before `pidcat` cuts the original `adb` output line so as to not miss any lines in grepping. Moreover, you can specify different colors for each word in these options, which is very helpful in checking different word terms in massive log in sophisticated debugging. Corresponding case-ignored options are also provided: `--igrep`, `--ihighlight`, `--igrev`
 * `--header-width`: if customized header added in each log line besides Android headers, this option can help indent additional space for each wrapped lines
 * `--tee`, `--tee-original`: it supports to output the filtered and un-filtered `pidcat` result to specified files, which is useful for checking later
 * `--pipe`: it supports the script running in a pipe mode. For example, ``adb -d logcat | pidcat --pipe `tput cols`
                        com.testapp``. This is very useful if you want to use 3rd party tool to filter adb output, such as grepping, highlighting. For example, ``adb -d logcat
                        | h -i 'battery' | pidcat --pipe `tput cols`
                        com.testapp``. [`h`][2] is a keyword hilight filter utility. The option needs the current terminal width provided as the parameter, which is easy to get in shell using command `` `tput cols` ``.

Here is an example of the output of the following command:

    pidcat --timestamp --header-width=15 --highlight="CDMA\|BATTERY\\magenta\|timeout\\white\|level=100\\cyan"

![Example screen](screen.png)

You could notice that
 * The words are highlighted in specified colors, even the cut words due to line wrapping (`--highlight`);
 * Timestamps are headed in each line (`--timestamp`);
 * Additional indentation spaces are added to align the wrapped lines to the right of timestamp headers (`--header-width`);

Here are details of all additional options provided:
<pre>
  --timestamp           Prepend each line of output with the current time.
  --extra-header-width N
                        Width of customized log header. If you have your own
                        header besides Android log header, this option will
                        further indent your wrapped lines with additional
                        width
  --grep GREP_WORDS     Filter lines with words in log messages. The words are
                        delimited with '\|', where each word can be tailed
                        with a color initialed with '\\'. If no color is
                        specified, 'RED' will be the default color. For
                        example, option --grep="word1\|word2\\CYAN" means to
                        filter out all lines containing either word1 or word2,
                        and word1 will appear in default color RED while word2
                        will be in CYAN. Supported colors (case ignored):
                        {BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN,
                        WHITE}
  --highlight HIGHLIGHT_WORDS
                        Words to highlight in log messages. Unlike --grep
                        option, this option will only highlight the specified
                        words with specified color but does not filter any
                        lines. Except this, the format and supported colors
                        are the same as --grep
  --grepv GREPV_WORDS   Exclude lines with words from log messages. The format
                        and supported colors are the same as --grep. Note that
                        if both --grepv and --grep are provided and they
                        contain the same word, the line will always show,
                        which means --grep overwrites --grepv for the same
                        word they both contain
  --igrep IGREP_WORDS   The same as --grep, just ignore case
  --ihighlight IHIGHLIGHT_WORDS
                        The same as --highlight, just ignore case
  --igrepv IGREPV_WORDS
                        The same as --grepv, just ignore case
  --keep-all-fatal      Do not filter any fatal logs from pidcat output. This
                        is quite helpful to avoid ignoring information about
                        exceptions, crash stacks and assertion failures
  --tee FILE_NAME       Besides stdout output, also output the filtered result
                        (after grep/grepv) to the file
  --tee-original ORIGINAL_FILE_NAME
                        Besides stdout output, also output the unfiltered
                        result (all pidcat-formatted lines) to the file
  --tee-adb ADB_OUTPUT_FILE_NAME
                        Output original adb result (raw adb output) to the
                        file
  --pipe TERMINAL_WIDTH_FOR_PIPE_MODE
                        Note: you need to give terminal width as the value,
                        just put "`tput cols`" here. When running in pipe
                        mode, the script will take input from "stdin" rather
                        than launching adb itself. The usage becomes something
                        like "adb -d logcat | pidcat --pipe `tput cols`
                        com.testapp". This is very useful when you want to
                        apply any third-party scripts on the adb output before
                        pidcat cutting each line, like using 3rd-party scripts
                        to grep or hilight with colors (such as using 'ack' or
                        'h' command) to keywords. For example, "adb -d logcat
                        | h -i 'battery' | pidcat --pipe `tput cols`
                        com.testapp"
</pre>

Install
-------

Get the script:

 * Download the `pidcat.py` and place it on your PATH.


Make sure that `adb` from the [Android SDK][3] is on your PATH. This script will
not work unless this is that case. That means, when you type `adb` and press
enter into your terminal something actually happens.

To include `adb` and other android tools on your path:

    export PATH=$PATH:<path to Android SDK>/platform-tools
    export PATH=$PATH:<path to Android SDK>/tools

Include these lines in your `.bashrc`, `.zshrc` or `.bash_profile`.

*Note:* `<path to Android SDK>` should be absolute and not relative.

 [1]: https://github.com/JakeWharton/pidcat
 [2]: https://github.com/paoloantinori/hhighlighter
 [3]: http://developer.android.com/sdk/
