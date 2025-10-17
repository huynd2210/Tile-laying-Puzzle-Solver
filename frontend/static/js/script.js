document.addEventListener('DOMContentLoaded', () => {
    // Main app state
    const state = {
        width: 4,
        height: 4,
        obstacles: [],
        libraries: {},
        currentLibrary: 'builtin',
        selectedPieces: [],
        board: null,
        editMode: 'obstacle',
        solution: null,
        solutions: [],
        currentSolutionIndex: 0,
        isSolving: false,
        designerPiece: {
            grid: [],
            cells: [],
            color: 'red',
            id: '',
            gridSize: 5  // 5x5 grid for piece designer
        }
    };

    // Modal references
    const pieceModal = new bootstrap.Modal(document.getElementById('pieceModal'));
    const libraryModal = new bootstrap.Modal(document.getElementById('libraryModal'));

    // DOM elements
    const elements = {
        boardWidth: document.getElementById('board-width'),
        boardHeight: document.getElementById('board-height'),
        generateButton: document.getElementById('generate-board'),
        board: document.getElementById('board'),
        solveButton: document.getElementById('solve-button'),
        clearButton: document.getElementById('clear-button'),
        randomButton: document.getElementById('random-obstacles'),
        resultMessage: document.getElementById('result-message'),
        solutionStats: document.getElementById('solution-stats'),
        solutionDetails: document.getElementById('solution-details'),
        piecesContainer: document.getElementById('pieces-container'),
        modeObstacle: document.getElementById('mode-obstacle'),
        modeView: document.getElementById('mode-view'),
        librarySelector: document.getElementById('library-selector'),
        renameLibraryBtn: document.getElementById('rename-library-btn'),
        deleteLibraryBtn: document.getElementById('delete-library-btn'),
        newLibraryBtn: document.getElementById('new-library-btn'),
        newPieceBtn: document.getElementById('new-piece-btn'),
        saveLibraryBtn: document.getElementById('save-library-btn'),
        savePieceBtn: document.getElementById('save-piece-btn'),
        libraryName: document.getElementById('library-name'),
        pieceId: document.getElementById('piece-id'),
        pieceColor: document.getElementById('piece-color'),
        pieceDesigner: document.getElementById('piece-designer'),
        clearPieceGridBtn: document.getElementById('clear-piece-grid'),
        centerPieceBtn: document.getElementById('center-piece')
    };

    // Initialize the app
    function init() {
        // Set up event listeners
        elements.generateButton.addEventListener('click', generateBoard);
        elements.solveButton.addEventListener('click', solvePuzzle);
        elements.clearButton.addEventListener('click', clearBoard);
        elements.randomButton.addEventListener('click', addRandomObstacles);
        document.getElementById('prev-solution').addEventListener('click', prevSolution);
        document.getElementById('next-solution').addEventListener('click', nextSolution);
        elements.modeObstacle.addEventListener('change', updateEditMode);
        elements.modeView.addEventListener('change', updateEditMode);
        elements.librarySelector.addEventListener('change', handleLibraryChange);
        elements.renameLibraryBtn.addEventListener('click', handleRenameLibrary);
        elements.deleteLibraryBtn.addEventListener('click', handleDeleteLibrary);
        elements.saveLibraryBtn.addEventListener('click', handleSaveLibrary);
        elements.savePieceBtn.addEventListener('click', handleSavePiece);
        elements.clearPieceGridBtn.addEventListener('click', clearPieceDesigner);
        elements.centerPieceBtn.addEventListener('click', centerPieceDesign);
        document.getElementById('load-saved-solution').addEventListener('click', loadSavedSolution);
        listSavedSolutions();
        
        // Initialize the piece designer grid
        initializePieceDesigner();
        
        // Fetch libraries and pieces
        fetchLibraries();
        
        // Generate initial board
        generateBoard();
    }
    async function listSavedSolutions() {
        try {
            const resp = await fetch('/api/solutions');
            if (!resp.ok) throw new Error('Failed to list saved solutions');
            const data = await resp.json();
            const selector = document.getElementById('saved-solution-selector');
            selector.innerHTML = '<option value="">-- Select saved solutions --</option>';
            if (data.success && Array.isArray(data.solutions) && data.solutions.length > 0) {
                data.solutions.forEach(s => {
                    const opt = document.createElement('option');
                    const libLabel = s.library || s.library_id || 'unknown';
                    const meta = `${s.name || s.id} (${libLabel}; ${s.board.width}x${s.board.height}, ${s.num_solutions} sol)`;
                    opt.value = s.id;
                    opt.textContent = meta;
                    selector.appendChild(opt);
                });
            } else {
                // No saved solutions yet: keep placeholder, no error
            }
        } catch (e) {
            console.warn('Saved solutions not available yet.');
            const selector = document.getElementById('saved-solution-selector');
            selector.innerHTML = '<option value="">-- No saved solutions --</option>';
        }
    }

    async function loadSavedSolution() {
        const id = document.getElementById('saved-solution-selector').value;
        if (!id) {
            alert('Please select a saved solutions entry first.');
            return;
        }
        try {
            const resp = await fetch(`/api/solutions/${id}`);
            if (!resp.ok) throw new Error('Failed to load saved solutions');
            const data = await resp.json();
            if (!data.success) throw new Error(data.message || 'Unknown error');
            const record = data.record;
            // Optional: show library name if provided
            if (record.library) {
                showMessage(`Loaded from "${record.library}" (${record.board.width}x${record.board.height})`, false);
            }
            // set board
            state.width = record.board.width;
            state.height = record.board.height;
            elements.boardWidth.value = state.width;
            elements.boardHeight.value = state.height;
            state.obstacles = record.board.obstacles || [];
            renderBoard();
            // set library and pieces
            state.currentLibrary = record.library_id || 'builtin';
            if (elements.librarySelector.value !== state.currentLibrary) {
                elements.librarySelector.value = state.currentLibrary;
                updateLibraryActions();
            }
            // saved record includes full solutions payload already serialized for UI consumption
            state.solutions = record.solutions || [];
            state.currentSolutionIndex = 0;
            const current = getCurrentSolution();
            state.solution = current;
            updateSolutionNav();
            displaySolution(current);
            // keep message concise; previous showMessage may already print
        } catch (e) {
            console.error('Error loading saved solutions:', e);
            showMessage('Error loading saved solutions: ' + e.message, true);
        }
    }

    // Update edit mode
    function updateEditMode() {
        if (elements.modeObstacle.checked) {
            state.editMode = 'obstacle';
        } else if (elements.modeView.checked) {
            state.editMode = 'view';
        }
    }

    // Generate board based on current width/height
    function generateBoard() {
        state.width = parseInt(elements.boardWidth.value) || 4;
        state.height = parseInt(elements.boardHeight.value) || 4;
        state.obstacles = [];
        
        renderBoard();
    }

    // Render the board with current state
    function renderBoard() {
        const board = elements.board;
        board.style.gridTemplateColumns = `repeat(${state.width}, 40px)`;
        board.innerHTML = '';
        
        for (let i = 0; i < state.height; i++) {
            for (let j = 0; j < state.width; j++) {
                const cell = document.createElement('div');
                cell.className = 'cell';
                cell.dataset.row = i;
                cell.dataset.col = j;
                
                // Check if this cell is an obstacle
                if (isObstacle(i, j)) {
                    cell.classList.add('obstacle');
                }
                
                // Add click handler for toggling obstacles
                cell.addEventListener('click', () => {
                    if (state.editMode === 'obstacle') {
                        toggleObstacle(i, j);
                    }
                });
                
                board.appendChild(cell);
            }
        }
    }

    // Check if a cell is an obstacle
    function isObstacle(row, col) {
        return state.obstacles.some(ob => ob[0] === row && ob[1] === col);
    }

    // Toggle obstacle state for a cell
    function toggleObstacle(row, col) {
        const index = state.obstacles.findIndex(ob => ob[0] === row && ob[1] === col);
        
        if (index >= 0) {
            // Remove obstacle
            state.obstacles.splice(index, 1);
        } else {
            // Add obstacle
            state.obstacles.push([row, col]);
        }
        
        renderBoard();
    }

    // Fetch all available libraries
    async function fetchLibraries() {
        try {
            const response = await fetch('/api/libraries');
            if (!response.ok) {
                console.warn('Libraries endpoint unavailable, defaulting to builtin');
                state.libraries = { builtin: { id: 'builtin', name: 'Built-in Pieces', editable: false } };
                updateLibrarySelector();
                fetchLibraryPieces('builtin');
                return;
            }
            
            state.libraries = await response.json();
            updateLibrarySelector();
            
            // Fetch pieces for the current library
            fetchLibraryPieces(state.currentLibrary);
        } catch (error) {
            console.warn('Error fetching libraries, defaulting to builtin');
            state.libraries = { builtin: { id: 'builtin', name: 'Built-in Pieces', editable: false } };
            updateLibrarySelector();
            fetchLibraryPieces('builtin');
        }
    }

    // Update the library selector dropdown
    function updateLibrarySelector() {
        const selector = elements.librarySelector;
        selector.innerHTML = '';
        
        // Add all libraries to the selector
        Object.values(state.libraries).forEach(library => {
            const option = document.createElement('option');
            option.value = library.id;
            option.textContent = library.name;
            selector.appendChild(option);
        });
        
        // Set the current library
        selector.value = state.currentLibrary;
        
        // Update library action buttons
        updateLibraryActions();
    }

    // Update the library action buttons (rename/delete)
    function updateLibraryActions() {
        const currentLib = state.libraries[state.currentLibrary];
        const isEditable = currentLib && currentLib.editable;
        
        elements.renameLibraryBtn.disabled = !isEditable;
        elements.deleteLibraryBtn.disabled = !isEditable;
        elements.newPieceBtn.disabled = !isEditable;
    }

    // Handle library change
    function handleLibraryChange() {
        state.currentLibrary = elements.librarySelector.value;
        updateLibraryActions();
        fetchLibraryPieces(state.currentLibrary);
    }

    // Handle renaming a library
    function handleRenameLibrary() {
        const currentLib = state.libraries[state.currentLibrary];
        if (!currentLib || !currentLib.editable) return;
        
        const newName = prompt('Enter new name for library:', currentLib.name);
        if (!newName) return;
        
        updateLibraryName(state.currentLibrary, newName);
    }

    // Update a library's name
    async function updateLibraryName(libraryId, newName) {
        try {
            const response = await fetch(`/api/libraries/${libraryId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name: newName })
            });
            
            if (!response.ok) {
                throw new Error('Failed to update library');
            }
            
            const result = await response.json();
            if (result.success) {
                // Update local state
                state.libraries[libraryId].name = newName;
                updateLibrarySelector();
                showMessage(`Library renamed to "${newName}"`, false);
            } else {
                throw new Error(result.message || 'Unknown error');
            }
        } catch (error) {
            console.error('Error updating library:', error);
            showMessage('Error renaming library: ' + error.message, true);
        }
    }

    // Handle deleting a library
    function handleDeleteLibrary() {
        const currentLib = state.libraries[state.currentLibrary];
        if (!currentLib || !currentLib.editable) return;
        
        if (!confirm(`Are you sure you want to delete the library "${currentLib.name}"?`)) {
            return;
        }
        
        deleteLibrary(state.currentLibrary);
    }

    // Delete a library
    async function deleteLibrary(libraryId) {
        try {
            const response = await fetch(`/api/libraries/${libraryId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error('Failed to delete library');
            }
            
            const result = await response.json();
            if (result.success) {
                // Update local state
                delete state.libraries[libraryId];
                
                // Switch to built-in library
                state.currentLibrary = 'builtin';
                updateLibrarySelector();
                fetchLibraryPieces('builtin');
                
                showMessage('Library deleted successfully', false);
            } else {
                throw new Error(result.message || 'Unknown error');
            }
        } catch (error) {
            console.error('Error deleting library:', error);
            showMessage('Error deleting library: ' + error.message, true);
        }
    }

    // Handle saving a new library
    function handleSaveLibrary() {
        const name = elements.libraryName.value.trim();
        if (!name) {
            alert('Please enter a library name');
            return;
        }
        
        createLibrary(name);
    }

    // Create a new library
    async function createLibrary(name) {
        try {
            const response = await fetch('/api/libraries', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name })
            });
            
            if (!response.ok) {
                throw new Error('Failed to create library');
            }
            
            const result = await response.json();
            if (result.success) {
                // Update local state
                state.libraries[result.library.id] = result.library;
                
                // Switch to the new library
                state.currentLibrary = result.library.id;
                updateLibrarySelector();
                
                // Clear the form and close the modal
                elements.libraryName.value = '';
                libraryModal.hide();
                
                // Fetch pieces for the new library (should be empty)
                fetchLibraryPieces(result.library.id);
                
                showMessage(`Library "${name}" created successfully`, false);
            } else {
                throw new Error(result.message || 'Unknown error');
            }
        } catch (error) {
            console.error('Error creating library:', error);
            showMessage('Error creating library: ' + error.message, true);
        }
    }

    // Fetch pieces for a specific library
    async function fetchLibraryPieces(libraryId) {
        try {
            const response = await fetch(`/api/libraries/${libraryId}/pieces`);
            if (!response.ok) {
                throw new Error('Failed to fetch pieces');
            }
            
            const pieces = await response.json();
            
            // Set all pieces as selected by default
            state.selectedPieces = Object.keys(pieces);
            console.log('All pieces selected by default:', state.selectedPieces);
            
            renderPieces(pieces, libraryId);
        } catch (error) {
            console.error('Error fetching pieces:', error);
            showMessage('Error loading pieces: ' + error.message, true);
        }
    }

    // Render available pieces in the UI
    function renderPieces(pieces, libraryId) {
        const container = elements.piecesContainer;
        container.innerHTML = '';
        
        if (Object.keys(pieces).length === 0) {
            container.innerHTML = '<p class="text-muted">No pieces available in this library.</p>';
            return;
        }
        
        Object.entries(pieces).forEach(([id, piece]) => {
            const pieceElement = document.createElement('div');
            pieceElement.className = 'piece';
            pieceElement.dataset.id = id;
            
            // Check if piece is selected (default is selected, so we mark as deselected if not in the array)
            if (!state.selectedPieces.includes(id)) {
                pieceElement.classList.add('deselected');
            } else {
                pieceElement.classList.add('selected');
            }
            
            // Create mini-grid to display piece shape
            const offsets = piece.offsets;
            
            // Debug the offsets and color
            console.log(`Piece ${id} offsets:`, offsets);
            console.log(`Piece ${id} color:`, piece.color);
            
            if (!offsets || offsets.length === 0) {
                console.warn(`Piece ${id} has no valid offsets!`);
                // Add a warning marker to the piece
                pieceElement.classList.add('empty-piece');
                
                // Create an empty 2x2 grid for invalid pieces
                const grid = document.createElement('div');
                grid.className = 'piece-grid';
                grid.style.gridTemplateColumns = `repeat(2, 20px)`;
                
                for (let i = 0; i < 4; i++) {
                    const cell = document.createElement('div');
                    cell.className = 'piece-cell';
                    grid.appendChild(cell);
                }
                
                pieceElement.appendChild(grid);
                
                // Add piece ID label
                const label = document.createElement('div');
                label.className = 'piece-label';
                label.textContent = id + ' (invalid)';
                pieceElement.appendChild(label);
                
                // Add to container and skip the rest of this iteration
                container.appendChild(pieceElement);
                return;
            }
            
            // Calculate dimensions for the piece grid
            const maxI = Math.max(...offsets.map(offset => offset[0])) + 1;
            const maxJ = Math.max(...offsets.map(offset => offset[1])) + 1;
            
            const grid = document.createElement('div');
            grid.className = 'piece-grid';
            grid.style.gridTemplateColumns = `repeat(${maxJ}, 20px)`;
            
            // Create and fill grid cells for the piece
            for (let i = 0; i < maxI; i++) {
                for (let j = 0; j < maxJ; j++) {
                    const cell = document.createElement('div');
                    cell.className = 'piece-cell';
                    
                    // Check if any offset matches this position
                    const hasCell = offsets.some(offset => {
                        return Array.isArray(offset) && 
                               offset.length === 2 && 
                               offset[0] === i && 
                               offset[1] === j;
                    });
                    
                    if (hasCell) {
                        cell.classList.add('filled');
                        // Ensure color is properly applied
                        if (piece.color) {
                            cell.classList.add(`color-${piece.color}`);
                            // Debug if a color class was added
                            console.log(`Added color class 'color-${piece.color}' to cell for piece ${id}`);
                        } else {
                            console.warn(`Piece ${id} has no color!`);
                            // Default to red if no color specified
                            cell.classList.add('color-red');
                        }
                    }
                    
                    grid.appendChild(cell);
                }
            }
            
            // Add piece ID label
            const label = document.createElement('div');
            label.className = 'piece-label';
            label.textContent = id;
            
            // Add delete button only for editable libraries
            const libMeta = state.libraries[libraryId];
            const canEdit = libMeta && libMeta.editable === true;
            if (libraryId !== 'builtin' && canEdit) {
                const actions = document.createElement('div');
                actions.className = 'piece-actions';
                
                const deleteBtn = document.createElement('button');
                deleteBtn.className = 'btn btn-danger';
                deleteBtn.innerHTML = '&times;';
                deleteBtn.title = 'Delete piece';
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    deletePiece(libraryId, id);
                });
                
                actions.appendChild(deleteBtn);
                pieceElement.appendChild(actions);
            }
            
            // Add click handler to toggle piece selection
            pieceElement.addEventListener('click', () => {
                togglePieceSelection(id);
            });
            
            pieceElement.appendChild(grid);
            pieceElement.appendChild(label);
            container.appendChild(pieceElement);
        });
    }

    // Toggle piece selection for solving
    function togglePieceSelection(pieceId) {
        const index = state.selectedPieces.indexOf(pieceId);
        const pieceElement = document.querySelector(`.piece[data-id="${pieceId}"]`);
        
        if (index >= 0) {
            // Deselect piece
            state.selectedPieces.splice(index, 1);
            pieceElement.classList.remove('selected');
            pieceElement.classList.add('deselected');
            console.log(`Piece ${pieceId} deselected. Selected pieces:`, state.selectedPieces);
        } else {
            // Select piece
            state.selectedPieces.push(pieceId);
            pieceElement.classList.remove('deselected');
            pieceElement.classList.add('selected');
            console.log(`Piece ${pieceId} selected. Selected pieces:`, state.selectedPieces);
        }
        
        // Update the UI
        updateSelectedPiecesUI();
    }

    // Delete a piece from a library
    async function deletePiece(libraryId, pieceId) {
        if (!confirm(`Are you sure you want to delete piece "${pieceId}"?`)) {
            return;
        }
        
        try {
            const response = await fetch(`/api/libraries/${libraryId}/pieces/${pieceId}`, {
                method: 'DELETE'
            });
            const result = await response.json().catch(() => ({ success: false }));
            if (!response.ok || !result.success) {
                const msg = (result && result.message) ? result.message : 'Failed to delete piece';
                throw new Error(msg);
            }
            
            if (result.success) {
                // Remove from selected pieces if it was selected
                const index = state.selectedPieces.indexOf(pieceId);
                if (index >= 0) {
                    state.selectedPieces.splice(index, 1);
                }
                
                // Refresh pieces
                fetchLibraryPieces(libraryId);
                showMessage(`Piece "${pieceId}" deleted successfully`, false);
            }
        } catch (error) {
            console.error('Error deleting piece:', error);
            showMessage('Error deleting piece: ' + error.message, true);
        }
    }

    // Initialize the piece designer grid
    function initializePieceDesigner() {
        const designer = elements.pieceDesigner;
        designer.style.gridTemplateColumns = `repeat(${state.designerPiece.gridSize}, 30px)`;
        designer.innerHTML = '';
        
        // Create the grid
        for (let i = 0; i < state.designerPiece.gridSize; i++) {
            for (let j = 0; j < state.designerPiece.gridSize; j++) {
                const cell = document.createElement('div');
                cell.className = 'designer-cell';
                cell.dataset.row = i;
                cell.dataset.col = j;
                
                // Click handler to toggle cell
                cell.addEventListener('click', () => {
                    toggleDesignerCell(i, j);
                });
                
                designer.appendChild(cell);
            }
        }
        
        // Reset designer piece state
        state.designerPiece.cells = [];
        elements.pieceId.value = '';
        elements.pieceColor.value = 'red';
        state.designerPiece.color = 'red';
    }

    // Toggle a cell in the piece designer
    function toggleDesignerCell(row, col) {
        const cells = state.designerPiece.cells;
        const index = cells.findIndex(cell => cell[0] === row && cell[1] === col);
        
        if (index >= 0) {
            // Remove cell
            cells.splice(index, 1);
        } else {
            // Add cell
            cells.push([row, col]);
        }
        
        // Update designer UI
        updateDesignerUI();
    }

    // Update the piece designer UI
    function updateDesignerUI() {
        const color = elements.pieceColor.value;
        const cells = state.designerPiece.cells;
        
        // Update all cells in the designer
        const designerCells = elements.pieceDesigner.querySelectorAll('.designer-cell');
        designerCells.forEach(cell => {
            const row = parseInt(cell.dataset.row);
            const col = parseInt(cell.dataset.col);
            
            // Remove all active and color classes
            cell.classList.remove('active');
            Object.keys(colorClasses).forEach(colorClass => {
                cell.classList.remove(colorClass);
            });
            
            // Check if this cell is active
            if (cells.some(c => c[0] === row && c[1] === col)) {
                cell.classList.add('active');
                cell.classList.add(`color-${color}`);
            }
        });
        
        // Update state
        state.designerPiece.color = color;
    }

    // Clear the piece designer
    function clearPieceDesigner() {
        state.designerPiece.cells = [];
        updateDesignerUI();
    }

    // Center the piece design
    function centerPieceDesign() {
        const cells = state.designerPiece.cells;
        if (cells.length === 0) return;
        
        // Find bounding box
        const minRow = Math.min(...cells.map(c => c[0]));
        const minCol = Math.min(...cells.map(c => c[1]));
        const maxRow = Math.max(...cells.map(c => c[0]));
        const maxCol = Math.max(...cells.map(c => c[1]));
        
        // Calculate dimensions
        const height = maxRow - minRow + 1;
        const width = maxCol - minCol + 1;
        
        // Calculate center of grid
        const centerRow = Math.floor(state.designerPiece.gridSize / 2);
        const centerCol = Math.floor(state.designerPiece.gridSize / 2);
        
        // Calculate offset to center the piece
        const rowOffset = centerRow - Math.floor(height / 2) - minRow;
        const colOffset = centerCol - Math.floor(width / 2) - minCol;
        
        // Apply offset to cells
        state.designerPiece.cells = cells.map(cell => [
            cell[0] + rowOffset,
            cell[1] + colOffset
        ]).filter(cell => 
            cell[0] >= 0 && cell[0] < state.designerPiece.gridSize &&
            cell[1] >= 0 && cell[1] < state.designerPiece.gridSize
        );
        
        // Update designer UI
        updateDesignerUI();
    }

    // Handle saving a new piece
    function handleSavePiece() {
        const id = elements.pieceId.value.trim();
        const color = elements.pieceColor.value;
        const cells = state.designerPiece.cells;
        
        // Validate inputs
        if (!id) {
            alert('Please enter a piece ID');
            return;
        }
        
        if (cells.length === 0) {
            alert('Please add at least one cell to the piece');
            return;
        }
        
        // Normalize cells for saving
        const normalizedCells = normalizeCells(cells);
        
        // Create the piece
        createPiece(state.currentLibrary, id, color, normalizedCells);
    }

    // Normalize cells for saving (shift to origin)
    function normalizeCells(cells) {
        if (cells.length === 0) return [];
        
        // Find minimum row and column
        const minRow = Math.min(...cells.map(c => c[0]));
        const minCol = Math.min(...cells.map(c => c[1]));
        
        // Shift all cells so that the minimum row and column are 0
        return cells.map(cell => [
            cell[0] - minRow,
            cell[1] - minCol
        ]);
    }

    // Create a new piece
    async function createPiece(libraryId, pieceId, color, cells) {
        try {
            const response = await fetch(`/api/libraries/${libraryId}/pieces`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: pieceId,
                    color: color,
                    cells: cells
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to create piece');
            }
            
            const result = await response.json();
            if (result.success) {
                // Clear the designer and close the modal
                clearPieceDesigner();
                pieceModal.hide();
                
                // Refresh pieces
                fetchLibraryPieces(libraryId);
                showMessage(`Piece "${pieceId}" created successfully`, false);
            } else {
                throw new Error(result.message || 'Unknown error');
            }
        } catch (error) {
            console.error('Error creating piece:', error);
            showMessage('Error creating piece: ' + error.message, true);
        }
    }

    // Clear the board (remove all obstacles)
    function clearBoard() {
        state.obstacles = [];
        renderBoard();
        clearSolution();
    }

    // Add random obstacles to the board
    function addRandomObstacles() {
        // Clear existing obstacles
        state.obstacles = [];
        
        // Calculate how many obstacles to add (roughly 15-25% of the board)
        const totalCells = state.width * state.height;
        const obstacleCount = Math.floor(totalCells * (Math.random() * 0.1 + 0.15));
        
        // Add random obstacles
        for (let i = 0; i < obstacleCount; i++) {
            let row, col;
            do {
                row = Math.floor(Math.random() * state.height);
                col = Math.floor(Math.random() * state.width);
            } while (isObstacle(row, col));
            
            state.obstacles.push([row, col]);
        }
        
        renderBoard();
        clearSolution();
    }

    // Solve the current puzzle
    async function solvePuzzle() {
        // Don't attempt to solve if already solving
        if (state.isSolving) return;
        
        try {
            state.isSolving = true;
            elements.solveButton.textContent = 'Solving...';
            elements.solveButton.classList.add('loading');
            
            // Clear previous solution
            clearSolution();
            
            // Prepare data to send to the server
            const data = {
                width: state.width,
                height: state.height,
                obstacles: state.obstacles,
                pieces: state.selectedPieces,
                library_id: state.currentLibrary,
                max_solutions: parseInt(document.getElementById('num-solutions').value) || 1,
                threads: (function(){
                    const v = parseInt(document.getElementById('solver-threads').value);
                    return isNaN(v) || v < 1 ? undefined : v;
                })(),
                dedupe_equivalent: document.getElementById('dedupe-equivalent').checked,
                persist: document.getElementById('persist-solutions').checked,
                save_name: document.getElementById('save-name').value || ''
            };
            
            // Send solve request to the server
            const response = await fetch('/api/solve', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error('Failed to solve puzzle');
            }
            
            const result = await response.json();
            
            if (result.success) {
                // result.solutions is an array of solution arrays
                state.solutions = Array.isArray(result.solutions) ? result.solutions : (result.solution ? [result.solution] : []);
                state.currentSolutionIndex = 0;
                updateSolutionNav();
                const current = getCurrentSolution();
                state.solution = current; // keep backwards compatibility in renderer
                displaySolution(current);
                let msg = `${state.solutions.length} solution(s) found.`;
                if (result.saved) {
                    msg += ` Saved (id: ${result.saved_id}).`;
                } else if (result.saved === false && result.save_error) {
                    msg += ` Save failed: ${result.save_error}`;
                }
                showMessage(msg, false);
            } else {
                showMessage(result.message || 'No solution found.', true);
            }
        } catch (error) {
            console.error('Error solving puzzle:', error);
            showMessage('Error solving puzzle: ' + error.message, true);
        } finally {
            state.isSolving = false;
            elements.solveButton.textContent = 'Solve Puzzle';
            elements.solveButton.classList.remove('loading');
        }
    }

    // Display the solution on the board
    function displaySolution(solution) {
        // Show solution statistics and solution nav if multiple
        elements.solutionStats.classList.remove('d-none');
        updateSolutionNav();
        elements.solutionDetails.innerHTML = '';
        
        // Create list items for solution details
        solution.forEach(piece => {
            const li = document.createElement('li');
            li.textContent = `Piece ${piece.id} (${piece.color}) covers ${piece.cells.length} cells`;
            elements.solutionDetails.appendChild(li);
        });
        
        // Update the board to show the solution
        const cells = elements.board.querySelectorAll('.cell');
        
        cells.forEach(cell => {
            const row = parseInt(cell.dataset.row);
            const col = parseInt(cell.dataset.col);
            
            // Clear any previous solution styling
            cell.textContent = '';
            
            // Skip obstacle cells
            if (isObstacle(row, col)) return;
            
            // Find which piece (if any) covers this cell
            const coveringPiece = solution.find(piece => 
                piece.cells.some(cellPos => cellPos[0] === row && cellPos[1] === col)
            );
            
            if (coveringPiece) {
                cell.textContent = coveringPiece.id;
                cell.className = `cell color-${coveringPiece.color}`;
            }
        });
    }

    function updateSolutionNav() {
        const nav = document.getElementById('solution-nav');
        const idx = document.getElementById('solution-index');
        if (state.solutions && state.solutions.length > 1) {
            nav.classList.remove('d-none');
            idx.textContent = `${state.currentSolutionIndex + 1} / ${state.solutions.length}`;
        } else {
            nav.classList.add('d-none');
            idx.textContent = '';
        }
    }

    function getCurrentSolution() {
        if (!state.solutions || state.solutions.length === 0) return null;
        return state.solutions[state.currentSolutionIndex];
    }

    function prevSolution() {
        if (!state.solutions || state.solutions.length <= 1) return;
        state.currentSolutionIndex = (state.currentSolutionIndex - 1 + state.solutions.length) % state.solutions.length;
        const current = getCurrentSolution();
        state.solution = current;
        displaySolution(current);
    }

    function nextSolution() {
        if (!state.solutions || state.solutions.length <= 1) return;
        state.currentSolutionIndex = (state.currentSolutionIndex + 1) % state.solutions.length;
        const current = getCurrentSolution();
        state.solution = current;
        displaySolution(current);
    }

    // Clear the current solution display
    function clearSolution() {
        state.solution = null;
        elements.solutionStats.classList.add('d-none');
        elements.resultMessage.classList.add('d-none');
        
        // Reset cell styling but keep obstacles
        renderBoard();
    }

    // Show a message in the results area
    function showMessage(message, isError) {
        const messageElement = elements.resultMessage;
        messageElement.textContent = message;
        messageElement.classList.remove('d-none', 'alert-info', 'alert-danger', 'alert-success');
        messageElement.classList.add(isError ? 'alert-danger' : 'alert-success');
    }

    // Helper object for color classes
    const colorClasses = {
        'color-red': true,
        'color-blue': true,
        'color-green': true,
        'color-yellow': true,
        'color-magenta': true,
        'color-cyan': true,
        'color-lightred': true,
        'color-lightblue': true,
        'color-lightgreen': true,
        'color-lightyellow': true,
        'color-lightmagenta': true,
        'color-lightcyan': true,
        'color-gray': true
    };

    // Update the UI based on selected pieces
    function updateSelectedPiecesUI() {
        // Update all piece elements to show correct selection state
        document.querySelectorAll('.piece').forEach(pieceEl => {
            const pieceId = pieceEl.dataset.id;
            if (state.selectedPieces.includes(pieceId)) {
                pieceEl.classList.add('selected');
                pieceEl.classList.remove('deselected');
            } else {
                pieceEl.classList.add('deselected');
                pieceEl.classList.remove('selected');
            }
        });
    }

    // Start the application
    init();
}); 