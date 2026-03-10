    def _add_loaded_bot_to_combos(self, bot_config_serializable: dict):
        """Añade un bot cargado dinámicamente a los QComboBoxes de selección, reconstruyendo las clases."""
        
        bot_name = bot_config_serializable['bot_name']
        bot_class_module_str = bot_config_serializable['bot_class_module']
        bot_class_name_str = bot_config_serializable['bot_class_name']
        model_class_name_str = bot_config_serializable['model_class_name']
        model_file_path = bot_config_serializable['model_file_path']
        weights_file_path = bot_config_serializable['weights_file_path']

        try:
            # Dinámicamente importar la clase del bot
            bot_module = importlib.import_module(bot_class_module_str)
            bot_class = getattr(bot_module, bot_class_name_str)

            # Dinámicamente importar la clase del modelo
            quartopy_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            if quartopy_root not in sys.path:
                sys.path.insert(0, quartopy_root)
            
            model_module_name = f"custom_model_added_{hash(model_file_path)}" # Nombre único para el módulo
            spec = importlib.util.spec_from_file_location(model_module_name, model_file_path)
            if spec is None:
                raise ImportError(f"No se pudo crear especificación para el módulo desde {model_file_path}")
            module_model = importlib.util.module_from_spec(spec)
            sys.modules[model_module_name] = module_model
            spec.loader.exec_module(module_model)
            model_class = getattr(module_model, model_class_name_str)

            # Reconstruir el bot_config con las referencias de clase reales
            bot_config_reconstructed = {
                'bot_name': bot_name,
                'bot_class': bot_class,
                'model_class': model_class,
                'model_file_path': model_file_path,
                'weights_file_path': weights_file_path,
            }
            self._loaded_bots[bot_name] = bot_config_reconstructed
            self._update_comboboxes_with_loaded_bots() # Actualizar los comboboxes
            self._save_bot_configs() # Guardar después de añadir
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            QMessageBox.critical(self, "Error al añadir bot", f"No se pudo añadir el bot dinámicamente: {e}
Detalles: {error_details}")