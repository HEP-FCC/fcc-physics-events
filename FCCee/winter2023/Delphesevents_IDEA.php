<html>
<head>
<title>winter2023 IDEA</title>

<style>
<?php include '../../style/main.css'; ?>
</style>
</head>

<?php
$txt_file    = file_get_contents('../../data/FCCee/Delphesevents_winter2023_IDEA.txt');
$rows        = explode("\n", $txt_file);
?>

<?php include 'topbar.php'; ?>

<body>

 
<?php


$lname=array('NO','Name','Nevents','Nweights',
             'Nfiles','Nbad','Neos','Size (GB)',
             'Output Path','Main Process','Final States',
             'Cross Section (pb)','K-factor','Matching eff');



$NbrCol 	= count($lname); // $NbrCol : le nombre de colonnes

foreach($rows as $row => $data)
  {
    //get row data
    $row_data = explode(',,', $data);

    for ($i=0; $i<$NbrCol-1; $i++)
      {
        $info[$row][$lname[$i+1]] = $row_data[$i]; 
      }
  }

$NbrLigne 	= count($info);  // $NbrLigne : le nombre de lignes

?>

<?php include '../../search.php'; ?>


<h2>Delphes FCCee Physic events winter2023 production (IDEA )</h2>
<input type="text" id="myInput" onkeyup="search()" placeholder="Search for names.." title="Type in a name">
<table id="myTable">
  <thead>
  <tr class="header">

  <?php
  for ($i=0; $i<$NbrCol; $i++)
    {
      ?>
      <th> <?php 
      echo $lname[$i] ;
      ?> 
      </th>
      <?php
    }
?>

  </tr>
</thead>
<tbody>

<?php
$no 	= 1;
$totale 	= 0;
$totalf 	= 0;

for ($i=0; $i<$NbrLigne-1; $i++) { 
  echo '<tr >';
  for ($j=0; $j<$NbrCol; $j++) {
    if ($j==0)echo '<td>'.$no.'</td>';
    else echo '<td>'.$info[$i][$lname[$j]].'</td>';
  }
  echo  '</tr>';
  $no++;
}
?>
</tbody>

<!--tfoot>
  <tr>
  <th colspan="4">TOTAL</th>
  <th><?=number_format($totale)?></th>
  <th><?=number_format($totalf)?></th>

  </tr>
</tfoot-->
</table>
</body>
</html>

