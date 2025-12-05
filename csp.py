import time
import csv
import os
import argparse


class PenjadwalanIrigasiCSP:
    def __init__(self, lahan, kapasitas_pompa, slot_waktu):
        self.lahan = lahan
        self.kapasitas_pompa = kapasitas_pompa
        self.slot_waktu = slot_waktu
       
        # --- 1. DEFINISI VARIABEL ---
        # Memecah durasi menjadi unit tugas kecil (per jam)
        self.variables = []
        for nama_petak, durasi in lahan.items():
            for i in range(durasi):
                self.variables.append((nama_petak, i))
       
        # --- 2. DEFINISI DOMAIN ---
        # Domain adalah index slot waktu yang tersedia
        self.domains = {var: list(range(len(slot_waktu))) for var in self.variables}
        self.n_assignments = 0 # Counter untuk laporan kinerja
        self._printed_schedule = False


    def is_consistent(self, assignment, var, value):
        """
        Mengecek apakah penempatan jadwal (value) untuk petak (var) valid
        sesuai constraint kapasitas dan non-overlapping.
        """
        petak_saat_ini, _ = var
        slot_index = value


        # CONSTRAINT A: KAPASITAS POMPA
        # Hitung berapa petak yang sudah dijadwalkan di jam (slot) ini
        jumlah_penggunaan_slot = 0
        for assigned_var, assigned_val in assignment.items():
            if assigned_val == slot_index:
                jumlah_penggunaan_slot += 1
       
        # Jika slot sudah penuh sesuai kapasitas pompa, tolak.
        if jumlah_penggunaan_slot >= self.kapasitas_pompa:
            return False


        # CONSTRAINT B: SATU PETAK TIDAK BISA DISIRAM 2 KALI DI JAM SAMA
        # (Cek apakah petak ini sudah punya jadwal lain di jam yang sama)
        for assigned_var, assigned_val in assignment.items():
            assigned_petak, _ = assigned_var
            if assigned_petak == petak_saat_ini and assigned_val == slot_index:
                return False


        return True


    def select_unassigned_variable(self, assignment, domains=None):
        """
        Heuristik MRV (Min Remaining Values) using (possibly pruned) domains:
        Pilih variabel yang belum dijadwalkan yang memiliki jumlah opsi valid paling sedikit.
        Tie-breaker: degree heuristic among variables of same petak.
        """
        domains = domains if domains is not None else self.domains
        unassigned = [v for v in self.variables if v not in assignment]
        if not unassigned:
            return None


        def count_legal_values(var):
            # legal values are values in current domains[var] that satisfy is_consistent
            cnt = 0
            for val in domains.get(var, []):
                if self.is_consistent(assignment, var, val):
                    cnt += 1
            return cnt


        candidates = []
        min_count = None
        for var in unassigned:
            cnt = count_legal_values(var)
            if min_count is None or cnt < min_count:
                min_count = cnt
                candidates = [var]
            elif cnt == min_count:
                candidates.append(var)


        if len(candidates) == 1:
            return candidates[0]


        def degree(var):
            petak, _ = var
            deg = 0
            for other in self.variables:
                if other not in assignment and other != var and other[0] == petak:
                    deg += 1
            return deg


        best = max(candidates, key=degree)
        return best


    def order_domain_values(self, var, assignment, domains=None):
        """
        Domain ordering:
        Return domain values in the current domain order.
        """
        domains = domains if domains is not None else self.domains
        # Return a shallow copy to avoid accidental domain modification.
        return list(domains.get(var, list(range(len(self.slot_waktu)))))


    def backtrack(self, assignment, domains=None, forward_checking=True):
        """
        Backtracking with optional forward checking.
        - domains: current snapshot of domains (dictionary)
        - forward_checking: whether to prune neighbor domains after assignment
        """
        if domains is None:
            # Make a fresh copy from base domains
            domains = {v: list(vals) for v, vals in self.domains.items()}


        # Base Case
        if len(assignment) == len(self.variables):
            return assignment


        # 1. Choose variable with MRV
        var = self.select_unassigned_variable(assignment, domains)


        # 2. Order domain values (default domain order)
        for value in self.order_domain_values(var, assignment, domains):
            if self.is_consistent(assignment, var, value):
                # tentatively assign
                assignment[var] = value
                self.n_assignments += 1


                if forward_checking:
                    # Clone domains for recursion so we can safely prune
                    new_domains = {v: list(vals) for v, vals in domains.items()}
                    # Set domain for var to the assigned value
                    new_domains[var] = [value]


                    # Prune neighbors: any value in other domains that becomes inconsistent should be removed
                    contradiction = False
                    for other in self.variables:
                        if other in assignment:
                            continue
                        allowed = []
                        for val in new_domains.get(other, []):
                            if self.is_consistent(assignment, other, val):
                                allowed.append(val)
                        new_domains[other] = allowed
                        if len(allowed) == 0:
                            contradiction = True
                            break


                    if not contradiction:
                        result = self.backtrack(assignment, new_domains, forward_checking)
                        if result is not None:
                            return result
                else:
                    # No forward checking: just recurse with a copy of domains to keep isolation
                    result = self.backtrack(assignment, {v: list(vals) for v, vals in domains.items()}, forward_checking)
                    if result is not None:
                        return result


                # failed deeper, undo assignment
                del assignment[var]


        return None # Gagal menemukan solusi di cabang ini


    def solve(self, print_console=True, forward_checking=True):
        """
        Run the CSP solver, optionally print the schedule, and return the assignment
        (or None if unsatisfiable). This method does not write files — file saving is handled
        by the CLI code in __main__ to support an interactive "iya/tidak" prompt.
        """
        print(f"Sedang mencari jadwal optimal untuk {len(self.lahan)} petak...")
        start_time = time.time()


        initial_domains = {v: list(vals) for v, vals in self.domains.items()}
        solution = self.backtrack({}, domains=initial_domains, forward_checking=forward_checking)


        end_time = time.time()
        duration = end_time - start_time


        if solution:
            print(f"Solusi Ditemukan dalam {duration:.4f} detik!")
            print(f"Total langkah assignment yang dicoba: {self.n_assignments}")


            if print_console:
                self.print_schedule(solution)
        else:
            print("\nTIDAK ADA SOLUSI YANG MEMENUHI CONSTRAINT.")
            print("Saran: Naikkan kapasitas pompa di 'pump_settings.csv' atau kurangi durasi siram.")


        # Return the solution to the caller (CLI can decide to save or not)
        return solution


    def print_schedule(self, solution, force=False):
        if self._printed_schedule and not force:
            return
        self._printed_schedule = True


        print("\n" + "="*60)
        print(" JADWAL IRIGASI OPTIMAL (CSP MANUAL)")
        print("="*60)
       
        # Mengelompokkan hasil berdasarkan slot waktu
        schedule_by_time = {i: [] for i in range(len(self.slot_waktu))}
        for var, slot_idx in solution.items():
            petak, _ = var
            schedule_by_time[slot_idx].append(petak)


        print(f"{'WAKTU':<15} | {'PETAK YANG DISIRAM'}")
        print("-" * 60)
       
        for i, time_str in enumerate(self.slot_waktu):
            petaks = schedule_by_time[i]
            if petaks:
                # Gabungkan nama petak, batasi agar tidak terlalu panjang di terminal
                petaks_str = ", ".join(petaks)
            else:
                petaks_str = "(Pompa Istirahat)"
            print(f"{time_str:<15} | {petaks_str}")
        print("-" * 60)


    def save_schedule_to_csv(self, solution, filename='schedule.csv', overwrite=False):
        """
        Save the schedule to a CSV file. Each row is a time slot, with the petaks scheduled in that slot.
        Arguments:
            solution: assignment dict {(petak, idx): slot_index}
            filename: desired filename (defaults to 'schedule.csv')
            overwrite: if True, allow overwriting an existing file; otherwise create timestamped copy
        """
        # Group by slot time
        schedule_by_time = {i: [] for i in range(len(self.slot_waktu))}
        for var, slot_idx in solution.items():
            petak, _ = var
            schedule_by_time[slot_idx].append(petak)


        # Ensure we do not overwrite unless allowed
        if os.path.exists(filename) and not overwrite:
            base, ext = os.path.splitext(filename)
            ts = time.strftime("%Y%m%d%H%M%S")
            filename = f"{base}_{ts}{ext}"


        # Write CSV: columns: slot_index, waktu, petak_disiram
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['slot_index', 'waktu', 'petak_disiram'])
                for i, time_str in enumerate(self.slot_waktu):
                    petaks = schedule_by_time.get(i, [])
                    petaks_str = ", ".join(petaks) if petaks else ""
                    writer.writerow([i, time_str, petaks_str])
            print(f"Jadwal disimpan ke '{filename}'")
        except Exception as e:
            print(f"Failed to save schedule to CSV: {e}")


# --- FUNGSI BANTUAN MEMBACA CSV ---
def load_data_from_csv():
    # 1. BACA DATA PLOTS (LAHAN)
    plots_data = {}
    try:
        with open('plots.csv', mode='r') as file:
            reader = csv.reader(file)
            next(reader) # Skip header
            for row in reader:
                if row:
                    # row[0] = Nama Petak, row[1] = Durasi
                    plots_data[row[0]] = int(row[1])
    except FileNotFoundError:
        print("Error: File 'plots.csv' tidak ditemukan! Pastikan file ada di folder yang sama.")
        exit()


    # 2. BACA DATA SETTING POMPA
    settings_data = {}
    try:
        with open('pump_settings.csv', mode='r') as file:
            reader = csv.reader(file)
            next(reader) # Skip header
            for row in reader:
                if row:
                    settings_data[row[0]] = int(row[1])
    except FileNotFoundError:
        print("Error: File 'pump_settings.csv' tidak ditemukan!")
        exit()


    # Generate Slot Waktu berdasarkan jam mulai & selesai
    start = settings_data.get('jam_mulai', 8)
    end = settings_data.get('jam_selesai', 12)
   
    time_slots = []
    for h in range(start, end):
        # Format jam "08:00 - 09:00"
        time_slots.append(f"{h:02d}:00 - {h+1:02d}:00")


    return plots_data, settings_data.get('kapasitas_pompa', 1), time_slots


# --- MAIN PROGRAM ---
if __name__ == "__main__":
    print("--- PROGRAM PENJADWALAN IRIGASI (AI - CSP) ---")
   
    # 1. Muat Data
    lahan, limit_pompa, jam_operasional = load_data_from_csv()


    print(f"Data Lahan         : {len(lahan)} petak")
    print(f"Kapasitas Pompa    : {limit_pompa} petak/jam")
    print(f"Jam Operasional    : {jam_operasional[0]} s.d {jam_operasional[-1]}")
   
    # Hitung total beban vs kapasitas
    total_beban = sum(lahan.values())
    total_kapasitas = len(jam_operasional) * limit_pompa
    print(f"Total Kebutuhan    : {total_beban} jam-petak")
    print(f"Kapasitas Tersedia : {total_kapasitas} slot")
   
    if total_beban > total_kapasitas:
        print("\nPERINGATAN: Kebutuhan melebihi kapasitas! Solusi mungkin tidak ada.")
    print("-" * 30)
   
    # ---------------------------
    # 2. CLI options and execute
    # ---------------------------
    parser = argparse.ArgumentParser(description='Penjadwalan irigasi menggunakan CSP (manual).')
    parser.add_argument('--save', action='store_true', help='Save the resulting schedule to CSV')
    parser.add_argument('--out', default='schedule.csv', type=str, help='Output CSV filename (default: schedule.csv)')
    parser.add_argument('--force', action='store_true', help='Overwrite existing output file if it exists')
    parser.add_argument('--quiet', action='store_true', help='Do not print the schedule to console')
    parser.add_argument('--no-fc', action='store_true', help='Disable forward checking (for performance comparisons)')
    args = parser.parse_args()


    # 3. Jalankan Solver
    app = PenjadwalanIrigasiCSP(lahan, limit_pompa, jam_operasional)
    solution = app.solve(print_console=not args.quiet, forward_checking=not args.no_fc)


    # If a solution exists, you'll either save automatically (args.save), or ask the user:
    if solution:
        # If the user passed --save, perform the save and skip prompting
        if args.save:
            app.save_schedule_to_csv(solution, filename=args.out, overwrite=args.force)
        else:
            # Prompt interactive: 'iya' or 'tidak'
            try:
                # Negative answers: 'tidak', 't', 'no', 'n'
                # Positive answers: 'iya', 'i', 'yes', 'y', 'ya'
                while True:
                    user_input = input("\nSimpan hasil ke CSV? (iya/tidak): ").strip().lower()
                    if user_input in ('iya', 'i', 'yes', 'y', 'ya'):
                        app.save_schedule_to_csv(solution, filename=args.out, overwrite=args.force)
                        break
                    elif user_input in ('tidak', 't', 'no', 'n'):
                        print("Simpan dibatalkan.")
                        break
                    else:
                        print("Jawaban tidak dimengerti. Masukkan 'iya' atau 'tidak'.")
            except (KeyboardInterrupt, EOFError):
                # If user presses Ctrl+C or script is non-interactive, just skip saving
                print("\nOperasi input dibatalkan — tidak menyimpan ke CSV.")



