<?php

/**
 * Description: Function parses command line arguments 
 * $opts    associative array of arguments
 */
function check_opts($opts)
{
    global $PROGRAM_OK, $ERR_PARAM, $DIRECTORY, $RECURSIVE, $PARSE_SCRIPT, $INT_SCRIPT, $PARSE_ONLY, $INT_ONLY, $XML_SCRIPT;
    if (array_key_exists("h", $opts) || array_key_exists("help", $opts))
    {
        if (count($opts) == 1)
        {
            echo "Script that runs parser.php and/or interpret.py scripts with test inputs
    -h or --help\tshows this message
    --directory\t\tdirectory to search tests in
    --recursive\t\tsearch tests in subdirectories of the test directory
    --parse-script\tpath to parse.php (will look in current directory
    \t\t\tif not set)
    --int-script\tpath to interpret.py (will look in current directory
    \t\t\tif not set)
    --parse-only\ttest parse.php only (cannot be set along with
    \t\t\t--int-only)
    --int-only\t\ttest interpret.py only (cannot be set along with
    \t\t\t--parse-only)
    --xml\t\tpath to xml comparer tool\n";
            exit($PROGRAM_OK);
        }
        else
        {
            exit($ERR_PARAM);
        }
    }
    if (array_key_exists("directory", $opts))
    {
        $DIRECTORY = $opts["directory"];
    }
    if (array_key_exists("recursive", $opts))
    {
        $RECURSIVE = true;
    }
    if (array_key_exists("parse-script", $opts))
    {
        $PARSE_SCRIPT = $opts["parse-script"];
    }
    if (array_key_exists("int-script", $opts))
    {
        $INT_SCRIPT = $opts["int-script"];
    }
    if (array_key_exists("parse-only", $opts) && array_key_exists("int-only", $opts))
    {
        exit($ERR_PARAM);
    }
    else if (array_key_exists("parse-only", $opts))
    {
        $PARSE_ONLY = true;
    }
    else if (array_key_exists("int-only", $opts))
    {
        $INT_ONLY = true;
    }
    
    if (array_key_exists("xml", $opts))
    {
        $XML_SCRIPT = $opts["xml"];
    }
}

/**
 * Description: Function that checks a suffix of a string
 * $haystack String
 * $needle Suffix
 */
function ends_with($haystack, $needle)
{
    $length = strlen($needle);
    if ($length == 0)
    {
        return true;
    }
    return (substr($haystack, -$length) === $needle);
}

/**
 * Description: Function that returns associative array of directories and files to be tested
 * $dir Directory to find tests in
 * $recursive Flag whether to find files recursively in subdirectories
 */
function get_files($dir, $recursive)
{
    if ($recursive == false)
    {
        return [$dir => glob($dir."/*.src")];
    }
    else
    {
        $rii = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($dir));
        $files = array(); 
        foreach ($rii as $file)
            {
            if ($file->isDir())
            { 
                continue;
            }
            if (ends_with($file->getPathname(), ".src"))
            {
                $files[$file->getPath()][] = $file->getPathname();
            }
        }
        return $files;
    }
}

/**
 * Description: Function that removes file extension
 * $file Path to a file
 */
function remove_extension($file)
{
    return pathinfo($file, PATHINFO_DIRNAME)."/".pathinfo($file, PATHINFO_FILENAME);
}

/**
 * Description: Function that returns whole path of a file
 * $file Path to a file without extension
 * $ext Extension to be concatenated to the file
 */
function get_full_path($file, $ext)
{
    return realpath($file . $ext);
}

/**
 * Description: Function that creates empty .out, .in, or .rc files
 * $filename Path to the test
 * $ext Extension of the file
 */
function create_empty_file($filename, $ext)
{
    global $ERR_OUTPUT_FILE;
    if ($ext == ".out" || $ext == ".in")
    {
        if (($file = fopen($filename.$ext, "w")) === false)
        {
            exit($ERR_OUTPUT_FILE);
        }
    }
    else if ($ext == ".rc")
    {
        if (($file = fopen($filename.$ext, "w")) === false)
        {
            echo "Error opening output file\n";
            exit($ERR_OUTPUT_FILE);
        }
        fwrite($file, "0");
        fclose($file);
    }
}

/**
 * Description: File that opens output file (.out, .in, .rc) or creates empty ones
 * $filename Path to the test
 * $ext Extension of the file
 */
function open_output_file($filename, $ext)
{

    if (file_exists($filename.$ext) === false)
    {
        create_empty_file($filename, $ext);
    }

    if (($file = fopen($filename.$ext, "r")) === false)
    {
        echo "Error opening output file\n";
        exit($ERR_OUTPUT_FILE);
    }
    return $file;
}

/**
 * Description: Function that creates an empty temporary file, writes input to it, and returns its stream
 * $input Input to be written to the temporary file
 */
function write_to_tmp_file($input)
{
    global $DIRECTORY, $ERR_RUNTIME;
    $tmp_file_name = tempnam($DIRECTORY, "out");
    if (($tmp_file = fopen($tmp_file_name, "w")) === false)
    {
        echo "Error opening temporary file\n";
        exit($ERR_RUNTIME);
    }
    fwrite($tmp_file, $input);
    fclose($tmp_file);
    return $tmp_file_name;
}

/**
 * Description: Creates one HTML table row for one test
 * $success Overall success of the test
 * $filename Name of the test
 * $expected_retval Return value taken from .rc file
 * $retval Actual return value from interpreter
 * $output_succ Bool value whether output matched
 * $expected_output Output taken from .out file
 * $output Output from interpreter
 */
function generate_test_html($success, $filename, $expected_retval, $retval, $output_succ, $expected_output, $output)
{
    $testname = pathinfo($filename.".src", PATHINFO_FILENAME);
    if ($success == true)
    {
        $html = '<tr><td class="succ">OK</td><td>'.$testname.'</td><td class="succ">OK</td><td class="succ">OK</td></tr>';
    }
    else
    {
        $html = '<tr><td class="fail">FAIL</td><td>'.$testname.'</td>';
        if ($expected_retval == $retval)
        {
            $html .= '<td class="succ">OK</td>';
        }
        else
        {
            $html .= '<td class="fail">FAIL Expected: '.$expected_retval.' Got: '.$retval.'</td>';
        }
        if ($output_succ)
        {
            $html .= '<td class="succ">OK</td></tr>';
        }
        else
        {
            $html .= '<td class="fail">FAIL Expected: '.$expected_output.'<br>Got: '.$output.'</td></tr>';
        }

    }
    return $html;
}

/**
 * Description: One --parse-only test
 * $filename Path to the test excluding file extension
 */
function test_parse($filename)
{
    global $PARSE_SCRIPT, $DIRECTORY, $ERR_OUTPUT_FILE, $XML_SCRIPT, $html_files;

    $success = true;
    $output_succ = true;
    fwrite(STDERR, 'php7.3 "' . $PARSE_SCRIPT . '" < "' . get_full_path($filename, ".src") . '"' . "\n");
    exec('php7.3 "' . $PARSE_SCRIPT . '" < "' . get_full_path($filename, ".src") . '"', $parse_output, $parse_retval);
    $parse_output = implode($parse_output);
    
    $file_out = open_output_file($filename, ".out");
    $file_rc = open_output_file($filename, ".rc");

    $expected_retval = stream_get_contents($file_rc);
    if ($expected_retval != $parse_retval)
    {
        $success = false;
    }

    if ($parse_retval == 0)
    {
        $tmp_file_name = write_to_tmp_file($parse_output);
        exec('java -jar "' . $XML_SCRIPT . '" "' . $tmp_file_name . '" "' . get_full_path($filename, ".out") . '"', $compare_xml_output, $compare_xml_retval);
        unlink($tmp_file_name);
        
        if ($compare_xml_retval != 0)
        {
            $success = false;
            $output_succ = false;
        }
    }


    fclose($file_out);
    fclose($file_rc);
    $html_files .= generate_test_html($success, $filename, $expected_retval, $parse_retval, $output_succ, "", "");
    return $success;
}

/**
 * Description: One --both test
 * $filename Path to the test excluding file extension
 */
function test_both($filename)
{
    global $PARSE_SCRIPT, $INT_SCRIPT, $html_files;
    $success = true;
    $output_succ = true;
    
    exec('php7.3 "' . $PARSE_SCRIPT . '" < "' . get_full_path($filename, ".src") . '"', $parse_output, $parse_retval);
    $parse_output = implode($parse_output);
    
    $file_rc = open_output_file($filename, ".rc");
    $expected_retval = stream_get_contents($file_rc);
    
    if ($parse_retval != 0)
    {
        if ($expected_retval != $parse_retval)
        {
            $success = false;
        }
        
        $html_files .= generate_test_html($success, $filename, $expected_retval, $parse_retval, $output_succ, "", "");
        return $success;
    }
    
    $file_in = open_output_file($filename, ".in");
    $file_out = open_output_file($filename, ".out");
    $expected_output = stream_get_contents($file_out);
    
    $tmp_file_name = write_to_tmp_file($parse_output);
    
    exec('python3 ' . $INT_SCRIPT . ' --source="' . $tmp_file_name . '" --input="' . $filename . '".in', $int_output, $int_retval);
    $int_output = implode("\n", $int_output);
    unlink($tmp_file_name);
    fclose($file_in);
    fclose($file_out);
    fclose($file_rc);

    if ($expected_retval != $int_retval)
    {
        $success = false;
    }
    if ($expected_output != $int_output && $int_retval == 0)
    {
        $success = false;
        $output_succ = false;
    }

    $html_files .= generate_test_html($success, $filename, $expected_retval, $int_retval, $output_succ, $expected_output, $int_output);            
    return $success;
}

/**
 * Description: One --int-only test
 * $filename Path to the test excluding file extension
 */
function test_int($filename)
{
    global $INT_SCRIPT, $html_files;
    $success = true;
    $output_succ = true;
    
    $file_rc = open_output_file($filename, ".rc");
    $expected_retval = stream_get_contents($file_rc);
    
    $file_in = open_output_file($filename, ".in");
    $file_out = open_output_file($filename, ".out");
    $expected_output = stream_get_contents($file_out);
        
    exec('python3 ' . $INT_SCRIPT . ' --source="' . get_full_path($filename, ".src") . '" --input="' . get_full_path($filename, ".in") . '"', $int_output, $int_retval);
    
    $int_output = implode($int_output);

    fclose($file_in);
    fclose($file_out);
    fclose($file_rc);
    
    if ($expected_retval != $int_retval)
    {
        $success = false;
    }
    if ($expected_output != $int_output && $int_retval == 0) 
    {
        $success = false;
        $output_succ = false;
    }

    $html_files .= generate_test_html($success, $filename, $expected_retval, $int_retval, $output_succ, $expected_output, $int_output);            
    return $success;
}

$ERR_PARAM = 10;
$ERR_INPUT_FILE = 11;
$ERR_OUTPUT_FILE = 12;
$ERR_HEADER = 21;
$ERR_OPCODE = 22;
$ERR_RUNTIME = 99;
$PROGRAM_OK = 0;

$DIRECTORY = ".";
$RECURSIVE = false;
$PARSE_SCRIPT = "parse.php";
$INT_SCRIPT = "interpret.py";
$PARSE_ONLY = false;
$INT_ONLY = false;
$XML_SCRIPT = "/pub/courses/ipp/jexamxml/jexamxml.jar";

$opts = getopt("h", array("help", "directory::", "recursive", "parse-script::", "int-script::", "parse-only", "int-only", "xml::"));
check_opts($opts);

$test_dirs = get_files($DIRECTORY, $RECURSIVE);

$html = '<html>
<head>
    <title>test.php report</title>
    <style>
    body {
        font-size: 16px;
        font-family: Arial, Helvetica, sans-serif;
    }
    .dir {
        background-color:rgb(238, 238, 238);
        padding: 5px;
        border-radius: 5px;
        margin-top: 6px;
        }
    .file {
        background-color: rgb(248, 248, 248);
        padding: 3px;
        margin-left: 5px;
        margin-top: 2px;
        border-radius: 5px;
        text-align: center;
    }
    .succ{
        color: seagreen;
    }
    .fail{
        color:maroon;
    }
    table {
        border-collapse: collapse;
    }
    table, th, td {
        border: 1px solid rgb(129, 129, 129);
        padding: 3px;
    }
    </style>
</head>
<body>';



$tests_in_dir = 0;
$tests_in_dir_pass = 0;
$tests_total = 0;
$tests_total_pass = 0;
$html_dirs = "";

foreach ($test_dirs as $dir => $files)
{
    $tests_in_dir = 0;
    $tests_in_dir_pass = 0;
    $html_files = "";
    foreach($files as $file)
    {
        $tests_in_dir++;
        $tests_total++;
        $success = true;

        $filename = remove_extension($file);
        fwrite(STDERR, "test.php: running test " . $filename . "\n");

        if ($PARSE_ONLY == true)
        {
            $success = test_parse($filename);
        }
        else if ($INT_ONLY == true)
        {
            $success = test_int($filename);
        }
        else
        {
            $success = test_both($filename);
        }

        if ($success)
        {
            $tests_in_dir_pass++;
            $tests_total_pass++;
        }
    }

    if ($tests_in_dir == 0)
    {
        $percent = "0";    
    }
    else
    {
        $percent = (string) round($tests_in_dir_pass/$tests_in_dir*100, 2);
    }
    $html_dirs .= '<div class="dir"> Directory: <b>' . $dir . '</b> Passed tests: '.$tests_in_dir_pass.'/'.$tests_in_dir.' ('.$percent.' %)
    <table class="file"><tr>
    <th>Status</th>
    <th>Test name</th>
    <th>Return code</th>
    <th>Output</th>
    </tr>'.$html_files.'</table></div>';
}

$percent = (string) round($tests_total_pass/$tests_total*100, 2);
$html .= '<h3>Total passed tests: '.$tests_total_pass.'/'.$tests_total.' ('.$percent.' %)</h3>'.$html_dirs.'</html>';
print($html);

?>
