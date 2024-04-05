      <div class="mt-5 input-group input-group-lg">
        <span class="input-group-text" id="sample-search-label">Name</span>
        <input type="text"
               class="form-control"
               id="sample-search-input"
               placeholder="Search in sample names..."
               aria-label="Search in sample names"
               aria-describedby="sample-search-label"
               onkeyup="search()">
      </div>

      <button type="button"
              class="btn btn-light float-end mt-4"
              id="table-expand-btn">Expand table</button>

      <table class="table table-striped table-hover mt-1" id="sample-table">
        <thead class="bg-blue">
          <tr class="header">
          <?php for ($i=0; $i < $NbrCol; $i++): ?>
            <th><?= $lname[$i] ?></th>
          <?php endfor ?>
          </tr>
        </thead>
        <tbody>
        <?php for ($i=0; $i < $NbrLigne-1; $i++): ?>
          <tr>
            <td><?= $i + 1; ?></td>
            <?php for ($j=1; $j < $NbrCol; $j++): ?>
            <td><?= $info[$i][$lname[$j]] ?></td>
            <?php endfor ?>
          </tr>
        <?php endfor ?>
        </tbody>
      </table>

      <script src="<?= BASE_URL ?>/js/table.js"></script>
