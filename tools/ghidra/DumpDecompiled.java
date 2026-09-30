// Decompiles every function into one text file. Argument: output file path.
//@category BopIt

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class DumpDecompiled extends GhidraScript {
	@Override
	public void run() throws Exception {
		File out = new File(getScriptArgs()[0]);
		DecompInterface decompiler = new DecompInterface();
		decompiler.openProgram(currentProgram);
		int done = 0;
		try (PrintWriter writer = new PrintWriter(new FileWriter(out))) {
			FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
			while (functions.hasNext() && !monitor.isCancelled()) {
				Function function = functions.next();
				if (function.isThunk() || function.isExternal()) {
					continue;
				}
				writer.println("// FUNCTION " + function.getName(true) + " @ " + function.getEntryPoint());
				DecompileResults results = decompiler.decompileFunction(function, 60, monitor);
				if (results.decompileCompleted()) {
					writer.println(results.getDecompiledFunction().getC());
				}
				else {
					writer.println("// decompile failed: " + results.getErrorMessage());
				}
				done++;
			}
		}
		decompiler.dispose();
		println("Decompiled " + done + " functions to " + out);
	}
}
