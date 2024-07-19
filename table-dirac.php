<?php
# Refresh sample DB
# if (time() - filemtime(SAMPLEDB_PATH) > 2 * 3600) {

if (!file_exists(AUGMENTSFILE_PATH)) {
  echo "<br>ERROR: Augments file not found!";
  return;
}

if (!file_exists(TRANSINFO_PATH)) {
  echo "<br>ERROR: Transformations info file not found!";
  return;
}

# Load augments
$json_string = file_get_contents(AUGMENTSFILE_PATH);
$augments = json_decode($json_string, true)['augments'];
# echo "<br><br>Augments:<br>";
# print_r($augments);

# Load transformations info
$phar = new \PharData(TRANSINFO_PATH);
$trans_info;
foreach (new \RecursiveIteratorIterator($phar) as $file) {
  if (str_ends_with($file, '.json')) {
    $json_string = file_get_contents($file->getPathName());
    $trans_info = json_decode($json_string, true);
    break;
  }
}
$last_update = $trans_info['last_file_update'];
$transformations = $trans_info['transformations'];
# echo "<br><br>Transformations:<br>";
# print_r($transformations);

$sample_db = array();
$sample_db['last_update'] = $last_update;
$sample_db['samples'] = array();
foreach ($transformations as $trans_id => $trans) {
  /*
  if (!array_key_exists($trans_id, $augments)) {

    # echo '<br>WARNING: Augments file does not contain sample: ' . $trans_id . '!';
    continue;
  }
  */

  $augment = array();
  if (array_key_exists($trans_id, $augments)) {
    $augment = $augments[$trans_id];
  }

  $sample = array();

  # Status
  $sample['status'] = strtolower($trans['Status']);

  # Name
  if (array_key_exists('name', $augment)) {
    $sample['name'] = $augment['name'];
  } else {
    $sample['name'] = 'Not assigned';
  }

  # Cross-section
  if (array_key_exists('cross-section', $augment)) {
    $sample['cross-section'] = $augment['cross-section'];
  } elseif (array_key_exists('cross-section', $trans)) {
    $sample['cross-section'] = $trans['cross-section'];
  }

  # Cross-section error
  if (array_key_exists('cross-section-error', $augment)) {
    $sample['cross-section-error'] = $augment['cross-section-error'];
  } elseif (array_key_exists('cross-section-error', $trans)) {
    $sample['cross-section-error'] = $trans['cross-section-error'];
  }

  # Efficiency
  if (array_key_exists('efficiency', $augment)) {
    $sample['efficiency'] = $augment['efficiency'];
  } else {
    $sample['efficiency'] = 1.;
  }

  # Efficiency info
  if (array_key_exists('efficiency-info', $augment)) {
    $sample['efficiency-info'] = $augment['efficiency-info'];
  } else {
    $sample['efficiency-info'] = '';
  }

  # Total sum of weights
  if (array_key_exists('total-sum-of-weights', $trans)) {
    $sample['total-sum-of-weights'] = $trans['total-sum-of-weights'];
  } else {
    $sample['total-sum-of-weights'] = 'Unknown';
  }

  # Total number of events
  $sample['total-number-of-events'] = $trans['total-number-of-events'];

  # Number of events per file
  $sample['number-of-events-per-file'] = $trans['number-of-events-per-file'];

  # Paths
  $sample['path'] = $trans['path'];

  # Production manager
  $cn = explode('/', $trans['production-manager'])[7];
  $name = explode('=', $cn)[1];
  $sample['production-manager'] = $name;

  $sample_db['samples'][$trans_id] = $sample;
}

file_put_contents(SAMPLEDB_PATH, json_encode($sample_db))

# }
?>


<?php
  $metadata = json_decode(file_get_contents(SAMPLEDB_PATH), true);
  $last_update = $metadata['last_update'];
  $samples = $metadata['samples'];
?>


      <p class="mt-3 mb-1 text-end text-secondary">Last update: <?= $last_update ?> UTC.</p>

      <div class="mt-5 mb-5 input-group input-group-lg">
        <span class="input-group-text" id="sample-search-label">Name</span>
        <input type="text"
               class="form-control"
               id="sample-search-input"
               placeholder="Search in sample names..."
               aria-label="Search in sample names"
               aria-describedby="sample-search-label"
               onkeyup="search()">
      </div>

      <div class="container">
        <?php foreach ($samples as $sample_id => $sample): ?>
        <div class="row mb-2">
          <div class="col sample-box">
            <div class="sample-top rounded bg-top-<?= strtolower($sample['status']) ?>">
              <div class="row">
                <!-- Name -->
                <div class="col p-3 text-left">
                  <b>Name</b><br>
                  <?= $sample["name"] ?>
                </div>
                <!-- Sample ID -->
                <div class="col p-3 text-left">
                  <b>Sample ID</b><br>
                  <?= $sample_id ?>
                </div>
                <!-- Status -->
                <div class="col p-3 text-left">
                  <b>Status</b><br>
                  <?= $sample["status"] ?>
                </div>
              </div>
              <div class="row">
                <div class="col p-3 text-left">
                  <b>Cross-section</b><br>
                  <?php
                    if (array_key_exists('cross-section', $sample) &&
                        array_key_exists('cross-section-error', $sample)) {
                      echo "{$sample['cross-section']} &pm; {$sample['cross-section-error']}";
                    } else {
                      echo 'Unknown';
                    } ?>
                </div>
                <div class="col p-3 text-left">
                  <b>Efficiency</b><br>
                  <?= $sample["efficiency"] ?><br>
                  <?php if ($sample["efficiency-info"] != "") {
                    echo $sample["efficiency-info"];
                  } ?>
                </div>
                <div class="col p-3 text-left">
                  <b>Total sum of weights</b><br>
                  <?= $sample["total-sum-of-weights"] ?>
                </div>
              </div>
            </div>
            <div class="sample-bottom rounded-bottom bg-bottom-<?= strtolower($sample['status']) ?>">
              <div class="row">
                <div class="col p-3 text-left">
                  <b>Total number of events</b><br>
                  <?= $sample["total-number-of-events"] ?>
                </div>
                <div class="col p-3 text-left">
                  <b>Number of events per file</b><br>
                  <?= $sample["number-of-events-per-file"] ?>
                </div>
              </div>
              <div class="row">
                <div class="col p-3 text-left">
                  <?php if (count($sample["path"]) > 1): ?>
                  <b>EOS Locations</b>
                  <?php else: ?>
                  <b>EOS Location</b>
                  <?php endif ?>
                  <ul>
                    <?php
                      foreach ($sample["path"] as $path) {
                        echo "<li>{$path}</li>";
                      }
                    ?>
                  </ul>
                </div>
                <div class="col p-3 text-left">
                  <b>Produced by</b><br>
                  <?= $sample["production-manager"] ?>
                </div>
              </div>
            </div>
          </div>
        </div>
        <?php endforeach ?>
      </div>


      <script src="<?= BASE_URL ?>/js/table-dirac.js"></script>
