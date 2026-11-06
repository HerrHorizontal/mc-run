// Convert HepMC ascii files (HepMC2 or HepMC3 format, as written by Herwig and Sherpa) into a
// single HepMC3 file in one of the following formats, which can all be read by Rivet:
//   root       HepMC3 ROOT TTree (WriterRootTree format), compressed with -c (default)
//   hepmc3     HepMC3 ascii (Asciiv3), uncompressed
//   hepmc3.gz  HepMC3 ascii (Asciiv3), gzip-compressed (level 9)
//
// usage: hepmc_convert [-f <format>] [-c <compression>] [-b <basket size>] <output> <input.hepmc> [...]
//
// -c: ROOT compression setting (100 * algorithm + level), default 209 (LZMA 9)
// -b: basket size of all branches in bytes, default 4 MiB (0: ROOT default)
//
// The number of events read from each input is checked against its event records ("E" lines),
// as the HepMC readers cannot distinguish a parsing error from the end of the file, and the
// number of events in the written file against the number of events read. Exits with a
// non-zero code on any error. Inputs have to be uncompressed ascii files.
#include "HepMC3/CompressedIO.h"
#include "HepMC3/GenEvent.h"
#include "HepMC3/ReaderFactory.h"
#include "HepMC3/WriterAscii.h"
#include "HepMC3/WriterRootTree.h"
#include "TBranch.h"
#include "TFile.h"
#include "TObjArray.h"
#include "TTree.h"
#include <cstdlib>
#include <exception>
#include <fstream>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

using namespace HepMC3;

static const char* tree_name = "hepmc3_tree";
static const char* branch_name = "hepmc3_event";
static const int gzip_level = 9;

// count the event records of a HepMC2 or HepMC3 ascii stream, each event starts with an "E " line
static long count_event_records(std::istream& stream) {
    long n_records = 0;
    std::string line;
    while (std::getline(stream, line))
        if (line.size() > 1 && line[0] == 'E' && line[1] == ' ') ++n_records;
    return stream.bad() ? -1 : n_records;
}

static long count_event_records(const std::string& path) {
    std::ifstream file(path);
    if (!file) return -1;
    return count_event_records(file);
}

// number of events in the written file
static long count_written_events(const std::string& format, const std::string& path) {
    if (format == "root") {
        std::unique_ptr<TFile> file(TFile::Open(path.c_str(), "READ"));
        auto tree = file ? file->Get<TTree>(tree_name) : nullptr;
        return tree ? tree->GetEntries() : -1;
    }
    // ascii, the HepMC3 input stream decompresses transparently
    HepMC3::ifstream file(path);
    if (!file) return -1;
    return count_event_records(file);
}

// create the writer of the output format, nullptr if the format is unknown
static std::shared_ptr<Writer> create_writer(const std::string& format, const std::string& output,
                                             std::shared_ptr<GenRunInfo> run_info, int compression,
                                             int basket_size) {
    if (format == "root") {
        auto writer = std::make_shared<WriterRootTree>(output, tree_name, branch_name, run_info);
        if (writer->failed()) return writer;
        // branches inherit the file compression when they are created inside the
        // WriterRootTree constructor, so set it on the file and on all branches
        writer->m_tree->GetCurrentFile()->SetCompressionSettings(compression);
        TIter next(writer->m_tree->GetListOfBranches());
        while (auto branch = static_cast<TBranch*>(next())) branch->SetCompressionSettings(compression);
        if (basket_size > 0) writer->m_tree->SetBasketSize("*", basket_size);
        return writer;
    }
    if (format == "hepmc3") return std::make_shared<WriterAscii>(output, run_info);
    if (format == "hepmc3.gz") {
        std::shared_ptr<std::ostream> stream =
            std::make_shared<HepMC3::ofstream>(output, Compression::z, gzip_level);
        return std::make_shared<WriterAscii>(stream, run_info);
    }
    return nullptr;
}

int main(int argc, char** argv) {
    std::string format = "root";
    int compression = 209;
    int basket_size = 4 * 1024 * 1024;
    std::vector<std::string> args;
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "-f" && i + 1 < argc) format = argv[++i];
        else if (arg == "-c" && i + 1 < argc) compression = std::atoi(argv[++i]);
        else if (arg == "-b" && i + 1 < argc) basket_size = std::atoi(argv[++i]);
        else args.push_back(arg);
    }
    if (args.size() < 2) {
        std::cerr << "usage: hepmc_convert [-f root|hepmc3|hepmc3.gz] [-c <compression>] [-b <basket size>] "
                  << "<output> <input.hepmc> [...]" << std::endl;
        return 1;
    }
    if (format != "root" && format != "hepmc3" && format != "hepmc3.gz") {
        std::cerr << "Unknown output format " << format << std::endl;
        return 1;
    }
    const std::string output = args[0];
    const std::vector<std::string> inputs(args.begin() + 1, args.end());
    // check that the output can be written before reading any input, the writers crash or throw
    // when they fail to open their file
    if (!std::ofstream(output)) {
        std::cerr << "Could not open output file " << output << std::endl;
        return 3;
    }

    std::shared_ptr<Writer> writer;
    long n_events = 0;
    for (const auto& input : inputs) {
        const long n_records = count_event_records(input);
        if (n_records < 0) {
            std::cerr << "Could not read " << input << std::endl;
            return 2;
        }
        std::shared_ptr<Reader> reader;
        try {
            reader = deduce_reader(input);
        } catch (const std::exception& e) {
            std::cerr << e.what() << std::endl;
        }
        if (!reader) {
            std::cerr << "Could not determine a HepMC reader for " << input << std::endl;
            return 2;
        }
        long n_file = 0;
        GenEvent evt;
        while (true) {
            reader->read_event(evt);
            if (reader->failed()) break;
            // create the writer after the first event, when the run info of the input is known
            if (!writer) {
                writer = create_writer(format, output, reader->run_info(), compression, basket_size);
                if (!writer || writer->failed()) {
                    std::cerr << "Could not open output file " << output << std::endl;
                    return 3;
                }
            }
            writer->write_event(evt);
            ++n_file;
        }
        reader->close();
        std::cout << "Read " << n_file << " events from " << input << std::endl;
        if (n_file != n_records) {
            std::cerr << "Read " << n_file << " events, but " << input << " contains " << n_records
                      << " event records!" << std::endl;
            // close the writer before exiting, destroying it at ROOT teardown crashes
            if (writer) writer->close();
            return 6;
        }
        n_events += n_file;
    }
    if (!writer || n_events == 0) {
        std::cerr << "No events found in the input files!" << std::endl;
        return 4;
    }
    writer->close();
    writer.reset();

    // verify the number of events in the written file
    const long n_written = count_written_events(format, output);
    if (n_written != n_events) {
        std::cerr << "Verification failed: expected " << n_events << " events in " << output << ", found "
                  << n_written << std::endl;
        return 5;
    }
    std::cout << "Wrote " << n_events << " events to " << output << " (format " << format;
    if (format == "root") std::cout << ", compression " << compression;
    std::cout << ")" << std::endl;
    return 0;
}
