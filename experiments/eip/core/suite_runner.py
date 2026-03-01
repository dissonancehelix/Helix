import argparse
import sys
import os
import suite_phase1
import suite_phase2
import suite_phase3
import suite_phase4
import suite_phase5
import suite_phase6
import suite_phase7
import suite_phase8
import suite_phase9
import suite_phase10
import suite_stress
import suite_hds
import suite_immediate_hostile
import sys
sys.path.append(r"c:\Users\dissonance\Desktop\DCP\02_EXPLORATORY")
import suite_exploratory
import datetime

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", type=int, default=1)
    args = parser.parse_args()
    
    ledger_path = r"c:\Users\dissonance\Desktop\DCP\01_STRUCTURAL_TESTS\PHASE_LEDGER.md"
    
    if args.phase == 1:
        success, res = suite_phase1.run_phase1()
        if not success:
            print("Phase 1 failed. Halting all execution.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                content = content.replace("| SUITE-01 | Numerical Integrity | PENDING | — | — |", f"| SUITE-01 | Numerical Integrity | FAIL | — | {datetime.datetime.now().isoformat()} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
            sys.exit(1)
        else:
            print("Phase 1 passed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                ts = datetime.datetime.now().isoformat()
                content = content.replace("| SUITE-01 | Numerical Integrity | PENDING | — | — |", f"| SUITE-01 | Numerical Integrity | PASS | HIGH | {ts} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
    elif args.phase == 2:
        success, res = suite_phase2.run_phase2()
        if not success:
            print("Phase 2 failed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                content = content.replace("| SUITE-02 | DCT Validation | PENDING | — | — |", f"| SUITE-02 | DCT Validation | FAIL | — | {datetime.datetime.now().isoformat()} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
        else:
            print("Phase 2 passed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                ts = datetime.datetime.now().isoformat()
                content = content.replace("| SUITE-02 | DCT Validation | PENDING | — | — |", f"| SUITE-02 | DCT Validation | PASS | HIGH | {ts} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
    elif args.phase == 3:
        success, res = suite_phase3.run_phase3()
        if not success:
            print("Phase 3 failed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                content = content.replace("| SUITE-03 | LIP & L* Validation | PENDING | — | — |", f"| SUITE-03 | LIP & L* Validation | FAIL | — | {datetime.datetime.now().isoformat()} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
        else:
            print("Phase 3 passed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                ts = datetime.datetime.now().isoformat()
                content = content.replace("| SUITE-03 | LIP & L* Validation | PENDING | — | — |", f"| SUITE-03 | LIP & L* Validation | PASS | HIGH | {ts} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
    elif args.phase == 4:
        success, res = suite_phase4.run_phase4()
        if not success:
            print("Phase 4 failed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                content = content.replace("| SUITE-04 | Anisotropic Extension | PENDING | — | — |", f"| SUITE-04 | Anisotropic Extension | FAIL | — | {datetime.datetime.now().isoformat()} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
        else:
            print("Phase 4 passed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                ts = datetime.datetime.now().isoformat()
                content = content.replace("| SUITE-04 | Anisotropic Extension | PENDING | — | — |", f"| SUITE-04 | Anisotropic Extension | PASS | HIGH | {ts} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
    elif args.phase == 5:
        success, res = suite_phase5.run_phase5()
        if not success:
            print("Phase 5 failed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                content = content.replace("| SUITE-05 | Tuple Operational Validity | PENDING | — | — |", f"| SUITE-05 | Tuple Operational Validity | FAIL | — | {datetime.datetime.now().isoformat()} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
        else:
            print("Phase 5 passed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                ts = datetime.datetime.now().isoformat()
                content = content.replace("| SUITE-05 | Tuple Operational Validity | PENDING | — | — |", f"| SUITE-05 | Tuple Operational Validity | PASS | HIGH | {ts} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
    elif args.phase == 6:
        success, res = suite_phase6.run_phase6()
        if not success:
            print("Phase 6 failed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                content = content.replace("| SUITE-06 | Planning Necessity | PENDING | — | — |", f"| SUITE-06 | Planning Necessity | FAIL | — | {datetime.datetime.now().isoformat()} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
        else:
            print("Phase 6 passed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                ts = datetime.datetime.now().isoformat()
                content = content.replace("| SUITE-06 | Planning Necessity | PENDING | — | — |", f"| SUITE-06 | Planning Necessity | PASS | HIGH | {ts} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
    elif args.phase == 7:
        success, res = suite_phase7.run_phase7()
        if not success:
            print("Phase 7 failed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                content = content.replace("| SUITE-07 | Multi-Agent Compression | PENDING | — | — |", f"| SUITE-07 | Multi-Agent Compression | FAIL | — | {datetime.datetime.now().isoformat()} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
        else:
            print("Phase 7 passed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                ts = datetime.datetime.now().isoformat()
                content = content.replace("| SUITE-07 | Multi-Agent Compression | PENDING | — | — |", f"| SUITE-07 | Multi-Agent Compression | PASS | HIGH | {ts} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
    elif args.phase == 8:
        success, res = suite_phase8.run_phase8()
        if not success:
            print("Phase 8 failed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                content = content.replace("| SUITE-08 | Global Consistency & Topology | PENDING | — | — |", f"| SUITE-08 | Global Consistency & Topology | FAIL | — | {datetime.datetime.now().isoformat()} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
        else:
            print("Phase 8 passed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                ts = datetime.datetime.now().isoformat()
                content = content.replace("| SUITE-08 | Global Consistency & Topology | PENDING | — | — |", f"| SUITE-08 | Global Consistency & Topology | PASS | HIGH | {ts} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
    elif args.phase == 9:
        success, res = suite_phase9.run_phase9()
        if not success:
            print("Phase 9 failed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                content = content.replace("| SUITE-09 | Cross-Domain Validation | PENDING | — | — |", f"| SUITE-09 | Cross-Domain Validation | FAIL | — | {datetime.datetime.now().isoformat()} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
        else:
            print("Phase 9 passed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                ts = datetime.datetime.now().isoformat()
                content = content.replace("| SUITE-09 | Cross-Domain Validation | PENDING | — | — |", f"| SUITE-09 | Cross-Domain Validation | PASS | HIGH | {ts} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
    elif args.phase == 10:
        success, res = suite_phase10.run_phase10()
        if not success:
            print("Phase 10 failed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                content = content.replace("| SUITE-10 | Self-Model Layer | PENDING | — | — |", f"| SUITE-10 | Self-Model Layer | FAIL | — | {datetime.datetime.now().isoformat()} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
        else:
            print("Phase 10 passed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                ts = datetime.datetime.now().isoformat()
                content = content.replace("| SUITE-10 | Self-Model Layer | PENDING | — | — |", f"| SUITE-10 | Self-Model Layer | PASS | HIGH | {ts} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
    elif args.phase == 11:
        success, res = suite_stress.run_stress_tests()
        if not success:
            print("STRESS TESTS failed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                content = content.replace("| STRESS-TESTS | STRESS TESTS | PENDING | — | — |", f"| STRESS-TESTS | STRESS TESTS | FAIL | — | {datetime.datetime.now().isoformat()} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
        else:
            print("STRESS TESTS passed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                ts = datetime.datetime.now().isoformat()
                content = content.replace("| STRESS-TESTS | STRESS TESTS | PENDING | — | — |", f"| STRESS-TESTS | STRESS TESTS | PASS | HIGH | {ts} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
    elif args.phase == 12:
        success, res = suite_hds.run_hds_tests()
        if not success:
            print("HOSTILE DOMAIN SUITE failed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                content = content.replace("| HOSTILE-SUITE | Hostile Domain Suite | PENDING | — | — |", f"| HOSTILE-SUITE | Hostile Domain Suite | FAIL | — | {datetime.datetime.now().isoformat()} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
        else:
            print("HOSTILE DOMAIN SUITE passed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                ts = datetime.datetime.now().isoformat()
                content = content.replace("| HOSTILE-SUITE | Hostile Domain Suite | PENDING | — | — |", f"| HOSTILE-SUITE | Hostile Domain Suite | PASS | HIGH | {ts} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
    elif args.phase == 13:
        success, res = suite_immediate_hostile.run_immediate_hostile_tests()
        if not success:
            print("IMMEDIATE HOSTILE SUITE failed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                content = content.replace("| IMMEDIATE-HOSTILE | Immediate Hostile Suite | PENDING | — | — |", f"| IMMEDIATE-HOSTILE | Immediate Hostile Suite | FAIL | — | {datetime.datetime.now().isoformat()} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
        else:
            print("IMMEDIATE HOSTILE SUITE passed.")
            if os.path.exists(ledger_path):
                with open(ledger_path, 'r') as f:
                    content = f.read()
                ts = datetime.datetime.now().isoformat()
                content = content.replace("| IMMEDIATE-HOSTILE | Immediate Hostile Suite | PENDING | — | — |", f"| IMMEDIATE-HOSTILE | Immediate Hostile Suite | PASS | HIGH | {ts} |")
                with open(ledger_path, 'w') as f:
                    f.write(content)
    elif args.phase == 14:
        success, res = suite_exploratory.run_exploratory_tests()
        if not success:
            print("EXPLORATORY BLOCK failed.")
        else:
            print("EXPLORATORY BLOCK passed.")
    else:
        print(f"Phase {args.phase} not implemented yet.")

if __name__ == '__main__':
    main()
