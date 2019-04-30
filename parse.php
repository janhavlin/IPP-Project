<?php
/**
 * parse.php
 * Creator: Jan Havlin, xhavli47@stud.fit.vutbr.cz
 * Description: Project 1 to the IPP course 2018/2019
 */

/**
 * Description: Function parses command line arguments 
 * $opts    associative array of arguments
 */
function check_opts($opts)
{
    global $PROGRAM_OK, $ERR_PARAM, $ERR_RUNTIME, $f_out_path, $f_out;
    if (array_key_exists("h", $opts) || array_key_exists("help", $opts))
    {
        if (count($opts) == 1)
        {
            echo "Script reads input code in IPPcode19 language from stdin and performs lexical and syntax analysis and outputs it to stdout as xml.\n
    -h or --help shows this message
    --stats=FILE if set with one of the following command, the script will output a file with stats
    --loc\t counts lines of code of the input
    --comments\t counts amount of comments
    --labels\t counts amount of labels
    --jumps\t counts amount of jump instructions (JUMP, JUMPIFEQ, JUMPIFNEQ)\n";
            exit($PROGRAM_OK);
        }
        else
        {
            exit($ERR_PARAM);
        }
    }
    else if (array_key_exists("loc", $opts) || array_key_exists("comments", $opts) || array_key_exists("labels", $opts) || array_key_exists("jumps", $opts))
    {
        if (array_key_exists("stats", $opts))
        {
            $f_out_path = $opts["stats"];
            if (($f_out = fopen($f_out_path, "w")) === false)
            {
                exit_program($ERR_OUTPUT);
            }
        }
        else
        {
            exit($ERR_PARAM);
        }
    }

}

/**
 * Description: Function prints stats of the input source code to an output file 
 * $opts            associative array of command line arguments
 * $line_counter    amount of lines of code
 * $comment_counter amount of comments
 * $label_counter   amount of label instructions
 * $jump_counter    amount of jump instructions
 * $f_out           output file 
 */
function print_stats()
{
    global $opts, $line_counter, $comment_counter, $label_counter, $jump_counter, $f_out;
    
    foreach ($opts as $opt => $key)
    {
        if      ($opt === "loc")     {fwrite($f_out, $line_counter . "\n");}
        else if ($opt === "comments"){fwrite($f_out, $comment_counter . "\n");}
        else if ($opt === "labels")  {fwrite($f_out, $label_counter . "\n");}
        else if ($opt === "jumps")   {fwrite($f_out, $jump_counter . "\n");}
    }

}

/**
 * Description: Function removes a comment (deletes everything after first occurance of '#')
 *              and trims a string (removes whitespace chars on both ends)
 * $string  string to be trimmed
 */
function remove_comment($string)
{
    global $comment_counter;
    if (strpos($string, "#") !== false)
    {
        $comment_counter++;
        $string = substr($string, 0, strpos($string, "#"));
    }
    $string = trim($string);
    return $string;
}

/**
 * Description: Checks whether string is a valid variable
 * $string  input string
 * $inst    xml object of current instruction
 */
function check_var($string, $inst)
{
    if (strlen($string) > 3 && (substr($string, 0, 3) === "GF@" || substr($string, 0, 3) === "LF@" || substr($string, 0, 3) === "TF@"))
    {
        // Regex: String begins and also ends by a sequence of at least one of the following chars: [a-z], [A-Z], [0-9], _, $, &, %, *, !, ?, -
        if (preg_match("/^[a-zA-Z_$&%*!?\-][a-zA-Z0-9_$&%*!?\-]*$/", substr($string, 3)) == true)
        {
            $arg = $inst->addChild("arg" . ($inst->count()+1), htmlspecialchars($string));
            $arg->addAttribute("type", "var");
            return true;
        }
    }
    return false;
}

/**
 * Description: Checks whether string is a valid symb
 * $string  input string
 * $inst    xml object of current instruction
 */
function check_symb($string, $inst)
{
    if (check_var($string, $inst))
    {
        return true;
    }
    else if ($string === "nil@nil" || $string === "bool@true" || $string === "bool@false")
    {
        $arg = $inst->addChild("arg" . ($inst->count()+1), substr($string, strpos($string, "@") + 1));
        $arg->addAttribute("type", substr($string, 0, strpos($string, "@")));
        return true;
    }
    else if ($string === "string@")
    {
        $arg = $inst->addChild("arg" . ($inst->count()+1), "");
        $arg->addAttribute("type", substr($string, 0, strpos($string, "@")));
        return true;        
    }
    else if (substr($string, 0, 4) === "int@")
    {
        // Regex: String begins with zero or one '-' followed by a sequence of at least one char [0-9] which is also the last char
        if (preg_match("/^[+-]?[0-9]+$/", substr($string, 4)) == true)
        {
            $arg = $inst->addChild("arg" . ($inst->count()+1), substr($string, strpos($string, "@") + 1));
            $arg->addAttribute("type", "int");
            return true;
        }
    }
    else if (substr($string, 0, 7) === "string@")
    {
        if (preg_match("/^([^\\\\]|(\\\\[0-9][0-9][0-9]))*$/", substr($string, 7)) == true)
        {
            $arg = $inst->addChild("arg" . ($inst->count()+1), htmlspecialchars(substr($string, strpos($string, "@") + 1)));
            $arg->addAttribute("type", "string");
            return true;
        }
    }

    return false;
}

/**
 * Description: Checks whether string is a valid symb
 * $string  input string
 * $inst    xml object of current instruction
 */
function check_label($string, $inst)
{
    if (preg_match("/^[a-zA-Z_$&%*!?\-][a-zA-Z0-9_$&%*!?\-]*$/", $string))
    {
        $arg = $inst->addChild("arg" . ($inst->count()+1), htmlspecialchars($string));
        $arg->addAttribute("type", "label");
        return true;
    }

    return false;
}

/**
 * Description: Checks whether string is a valid type
 * $string  input string
 * $inst    xml object of current instruction
 */
function check_type($string, $inst)
{
    if ($string === "int" || $string === "string" || $string === "bool")
    {
        $arg = $inst->addChild("arg" . ($inst->count()+1), $string);
        $arg->addAttribute("type", "type");
        return true;
    }

    return false;
}

/**
 * Description: Checks whether the input code header is correct
 * $line    line of code
 */
function check_header($line)
{
    global $ERR_HEADER, $PROGRAM_OK;
    if(substr(strtoupper($line), 0, 10) === ".IPPCODE19")
    {
        $line = remove_comment($line);
        if (strtoupper($line) === ".IPPCODE19")
        {
            return $PROGRAM_OK;
        }
    }
    return $ERR_HEADER;
}

/**
 * Description: Parses a line of code
 * $line    line of code
 */
function check_line($line)
{
    global $ERR_OPCODE, $ERR_OTHER, $PROGRAM_OK, $line_counter, $xml, $label_counter, $jump_counter, $labels;
    $line = remove_comment($line);
    if(strlen($line) == 0)
    {
        return $PROGRAM_OK;
    }
    $line_split = preg_split('/[\s]+/', $line);
    $inst = $xml->addChild("instruction");

    $opcode = strtoupper($line_split[0]); 
    switch ($opcode){
        //0 args:
        case "CREATEFRAME":
        case "PUSHFRAME":
        case "POPFRAME":
        case "RETURN":
        case "BREAK":
            if (count($line_split) == 1){break;}
            else {return $ERR_OTHER;}
            
        //1 arg: var
        case "DEFVAR":
        case "POPS":
            if (count($line_split) == 2 && check_var($line_split[1], $inst)){break;}
            else {return $ERR_OTHER;}  

        //1 arg: label
        case "LABEL":
            if (!in_array($line_split[1], $labels))
            {
                $label_counter++;
                $labels[] = $line_split[1];
            }
        case "JUMP":
            if ($opcode == "JUMP"){$jump_counter++;}
        case "CALL":
            if (count($line_split) == 2 && check_label($line_split[1], $inst)){break;}
            else {return $ERR_OTHER;}

        //1 arg: symb
        case "PUSHS":
        case "WRITE":
        case "EXIT":
        case "DPRINT":
            if (count($line_split) == 2 && check_symb($line_split[1], $inst)){break;}
            else {return $ERR_OTHER;}

        //2 args: var symb
        case "MOVE":
        case "INT2CHAR":
        case "STRLEN":
        case "TYPE":
        case "NOT":
            if (count($line_split) == 3 && check_var($line_split[1], $inst) && check_symb($line_split[2], $inst)){break;}
            else {return $ERR_OTHER;}

        //2 args: var type
        case "READ":
            if (count($line_split) == 3 && check_var($line_split[1], $inst) && check_type($line_split[2], $inst)){break;}
            else {return $ERR_OTHER;}

        //3 args: var symb symb
        case "ADD":
        case "SUB":
        case "MUL":
        case "IDIV":
        case "LT":
        case "GT":
        case "EQ":
        case "AND":
        case "OR":
        case "STRI2INT":
        case "CONCAT":
        case "GETCHAR":
        case "SETCHAR":
            if (count($line_split) == 4 && check_var($line_split[1], $inst) && check_symb($line_split[2], $inst) && check_symb($line_split[3], $inst)){break;}
            else {return $ERR_OTHER;}

        //3 args: label symb symb
        case "JUMPIFEQ":
        case "JUMPIFNEQ":
            $jump_counter++;
            if (count($line_split) == 4 && check_label($line_split[1], $inst) && check_symb($line_split[2], $inst) && check_symb($line_split[3], $inst)){break;}
            else {return $ERR_OTHER;}
        
        // Invalid operation code
        default:
            return $ERR_OPCODE;
            break;
        }
        
    $inst->addAttribute("order", ++$line_counter);
    $inst->addAttribute("opcode", strtoupper($line_split[0]));
    return $PROGRAM_OK;
}

/**
 * Description: Exits the script in case of an error
 * $status  error code
 */
function exit_program($status)
{
    global $f, $f_out, $line_count;
    if ($f)
    {
        fclose($f);
    }
    if ($f_out)
    {
        fclose($f_out);
    }
    echo "Error " . $status . " on line " . $line_count . "\n";
    exit($status);
}

$opts = getopt("h", array("help", "stats::", "loc", "comments", "labels", "jumps"));
check_opts($opts);


$ERR_PARAM = 10;
$ERR_INPUT = 11;
$ERR_OUTPUT = 12;
$ERR_HEADER = 21;
$ERR_OPCODE = 22;
$ERR_OTHER = 23;
$PROGRAM_OK = 0;

if (($f = fopen("php://stdin", "r")) === false)
{
    exit_program($ERR_INPUT);
}

$line_counter = 0;
$comment_counter = 0;
$label_counter = 0;
$jump_counter = 0;
$labels = array();

$xml = new SimpleXMLElement('<?xml version="1.0" encoding="UTF-8"?><program/>');
$xml->addAttribute("language", "IPPcode19");

$line = fgets($f);
$line_count = 1;
if (check_header($line) == $ERR_HEADER)
{
    exit_program($ERR_HEADER);
}

while($line = fgets($f))
{
    $line_count++;
    $err = check_line($line);
    if ($err != $PROGRAM_OK)
    {
        exit_program($err);
    }
}

print_stats();
fclose($f);
print($xml->asXML());
exit($PROGRAM_OK);
?>
